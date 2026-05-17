#!/usr/bin/env python3
"""
Batch Product Image Generator
Generate multiple product images with variations for e-commerce catalogs.

Usage:
    python3 scripts/run_product_batch.py --workflow workflows/batch_generation/sdxl_batch_product.json \
        --csv products.csv --parallel 3 --output-dir ./outputs

CSV Format:
    product_id,main_prompt,lifestyle_prompt,detail_prompt,negative_prompt,seed
"""

import argparse
import csv
import json
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

# Add scripts directory to path for _common import
sys.path.insert(0, str(Path(__file__).parent))

from _common import (
    http_get, http_post, is_cloud_host, resolve_api_key,
    build_cloud_aware_url, safe_path_join, coerce_seed
)


DEFAULT_LOCAL_HOST = "http://127.0.0.1:8188"
DEFAULT_CLOUD_HOST = "https://cloud.comfy.org"
ENV_API_KEY = "COMFY_CLOUD_API_KEY"


def load_product_csv(csv_path: str) -> list[dict]:
    """Load products from CSV file."""
    products = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)
    return products


def get_host_url(host: str | None, cloud: bool) -> str:
    """Determine host URL."""
    if host:
        return host
    if cloud:
        return DEFAULT_CLOUD_HOST
    return DEFAULT_LOCAL_HOST


def get_auth_headers(host: str, api_key: str | None) -> dict:
    """Get authorization headers."""
    headers = {}
    if is_cloud_host(host):
        key = api_key or resolve_api_key(None)
        if key:
            headers["X-API-Key"] = key
    return headers


def submit_prompt(workflow: dict, args: dict, host: str, api_key: str | None = None) -> str:
    """
    Submit a workflow prompt and return the prompt_id.
    """
    # Inject args into workflow
    prompt = inject_args(workflow, args)
    
    headers = get_auth_headers(host, api_key)
    headers["Content-Type"] = "application/json"
    
    url = build_cloud_aware_url(host, "/api/prompt")
    
    payload = {"prompt": prompt, "client_id": str(uuid.uuid4())}
    
    resp = http_post(url, json=payload, headers=headers)
    data = resp.json()
    
    if resp.status_code != 200:
        raise Exception(f"Submit failed: {resp.status_code} - {data}")
    
    return data.get("prompt_id", "")


def inject_args(workflow: dict, args: dict) -> dict:
    """Inject runtime args into workflow."""
    prompt = json.loads(json.dumps(workflow))  # Deep copy
    
    for node_id, node in prompt.get("nodes", {}).items():
        for key, value in node.get("inputs", {}).items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                arg_key = value[1:-1]
                if arg_key in args:
                    node["inputs"][key] = args[arg_key]
            elif isinstance(value, dict):
                for subkey, subval in value.items():
                    if isinstance(subval, str) and subval.startswith("{") and subval.endswith("}"):
                        arg_key = subval[1:-1]
                        if arg_key in args:
                            node["inputs"][key][subkey] = args[arg_key]
                # Handle seed dict: {"seed": -1, "control_after_generate": "increment"}
                if "seed" in value and isinstance(value["seed"], dict):
                    if "seed" in args:
                        node["inputs"][key]["seed"] = args["seed"]
    
    return prompt


def wait_for_completion(prompt_id: str, host: str, timeout: int = 600) -> tuple:
    """
    Wait for prompt completion via WebSocket or polling.
    Returns (success, outputs).
    """
    # Simple polling implementation
    headers = get_auth_headers(host, None)
    
    start_time = time.time()
    check_interval = 2
    
    while time.time() - start_time < timeout:
        # Check history for completed prompt
        if is_cloud_host(host):
            url = build_cloud_aware_url(host, "/api/history_v2/" + prompt_id)
        else:
            url = f"{host}/history/{prompt_id}"
        
        resp = http_get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            if prompt_id in data:
                prompt_data = data[prompt_id]
                outputs = []
                for node_id, node_output in prompt_data.get("outputs", {}).items():
                    for output_type, output_value in node_output.items():
                        if isinstance(output_value, list) and len(output_value) > 0:
                            if isinstance(output_value[0], dict) and "filename" in output_value[0]:
                                outputs.extend(output_value)
                return (True, outputs)
        
        time.sleep(check_interval)
    
    return (False, "Timeout waiting for completion")


def download_outputs(outputs: list, output_dir: str, host: str) -> list:
    """Download output images."""
    downloaded = []
    headers = get_auth_headers(host, None)
    
    os.makedirs(output_dir, exist_ok=True)
    
    for output in outputs:
        if "filename" in output:
            filename = output["filename"]
            subfolder = output.get("subfolder", "")
            
            # Build URL
            if is_cloud_host(host):
                url = build_cloud_aware_url(host, f"/api/view/{filename}")
                if subfolder:
                    url += f"?subfolder={subfolder}"
            else:
                url = f"{host}/view"
                params = f"?filename={filename}"
                if subfolder:
                    params += f"&subfolder={subfolder}"
                url += params
            
            # Download
            try:
                resp = http_get(url, headers=headers, stream=True)
                if resp.status_code == 200:
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            f.write(chunk)
                    downloaded.append(filepath)
            except Exception as e:
                print(f"  Warning: Failed to download {filename}: {e}")
    
    return downloaded


def generate_product_batch(
    workflow_path: str,
    products: list[dict],
    host: str,
    output_dir: str,
    parallel: int = 3,
    randomize_seed: bool = True,
    api_key: str | None = None
) -> dict:
    """
    Generate batch product images from CSV input.
    """
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    results = []
    completed = 0
    errors = 0
    
    for i, product in enumerate(products):
        product_id = product.get('product_id', f'product_{i+1}')
        print(f"\n[{i+1}/{len(products)}] Processing: {product_id}")
        
        # Build args from CSV row, with defaults
        args = {
            "main_product_prompt": product.get('main_prompt', product.get('main_product_prompt', 'product photography')),
            "lifestyle_prompt": product.get('lifestyle_prompt', 'lifestyle product shot'),
            "detail_prompt": product.get('detail_prompt', 'product detail close-up'),
            "negative_prompt": product.get('negative_prompt', 'watermark, text, logo, blurry, low quality'),
            "steps": int(product.get('steps', 30)),
        }
        
        # Handle seed
        if randomize_seed:
            args["seed"] = -1
        elif 'seed' in product and product['seed']:
            args["seed"] = int(product['seed'])
        
        try:
            prompt_id = submit_prompt(workflow, args, host, api_key)
            print(f"  Submitted: {prompt_id}")
            
            success, outputs = wait_for_completion(prompt_id, host, timeout=600)
            
            if success:
                product_output_dir = os.path.join(output_dir, product_id)
                os.makedirs(product_output_dir, exist_ok=True)
                downloaded = download_outputs(outputs, product_output_dir, host)
                print(f"  Completed: {len(downloaded)} images saved")
                results.append({
                    "product_id": product_id,
                    "status": "success",
                    "outputs": downloaded
                })
                completed += 1
            else:
                print(f"  Failed: {outputs}")
                results.append({
                    "product_id": product_id,
                    "status": "failed",
                    "error": outputs
                })
                errors += 1
                
        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "product_id": product_id,
                "status": "error",
                "error": str(e)
            })
            errors += 1
        
        # Rate limiting between submits
        time.sleep(1)
    
    return {
        "total": len(products),
        "completed": completed,
        "errors": errors,
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description='Batch Product Image Generator')
    parser.add_argument('--workflow', required=True, help='Path to workflow JSON')
    parser.add_argument('--csv', required=True, help='CSV file with product prompts')
    parser.add_argument('--host', default=None, help='ComfyUI host (auto-detected if not set)')
    parser.add_argument('--output-dir', default='./outputs/batch', help='Output directory')
    parser.add_argument('--parallel', type=int, default=3, help='Max parallel jobs')
    parser.add_argument('--randomize-seed', action='store_true', help='Use random seeds')
    parser.add_argument('--cloud', action='store_true', help='Use Comfy Cloud')
    parser.add_argument('--api-key', help='Comfy Cloud API key (or set COMFY_CLOUD_API_KEY)')
    
    args = parser.parse_args()
    
    # Setup host
    host = get_host_url(args.host, args.cloud)
    print(f"Using host: {host}")
    
    # Setup output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load products
    print(f"Loading products from: {args.csv}")
    products = load_product_csv(args.csv)
    print(f"Found {len(products)} products")
    
    # Generate
    print(f"\nStarting batch generation (parallel={args.parallel})...")
    summary = generate_product_batch(
        args.workflow,
        products,
        host,
        args.output_dir,
        args.parallel,
        args.randomize_seed,
        args.api_key
    )
    
    # Print summary
    print("\n" + "="*50)
    print("BATCH SUMMARY")
    print("="*50)
    print(f"Total:    {summary['total']}")
    print(f"Completed: {summary['completed']}")
    print(f"Errors:    {summary['errors']}")
    print(f"Output:    {args.output_dir}")
    
    # Save summary
    summary_path = os.path.join(args.output_dir, 'batch_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary:  {summary_path}")


if __name__ == '__main__':
    main()
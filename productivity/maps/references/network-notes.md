# maps_client.py — 环境注意事项

## Nominatim urllib 阻断问题

**现象**: 从这台机器（macOS, Python stdlib urllib）直接调用 Nominatim API，返回 `HTTP error` 或 `Connection reset by peer`，重试3次全部失败。

**验证**:
```bash
# Nominatim — 失败
curl -s --max-time 5 "https://nominatim.openstreetmap.org/search?q=Shenzhen&format=json&limit=1"

# OSRM — 正常
curl -s --max-time 8 "https://router.project-osrm.org/route/v1/driving/113.9,22.5;121.4,31.2?overview=false"
# → {"code":"Ok","routes":[{"distance":...}]}
```

**结论**: OSRM 路由可用。Nominatim 在此机器上被 IP 限流或阻断。

**当前 workaround**: 所有需要 geocode 的命令（`supplier-geo`, `logistics-cost`, `delivery-heatmap`）对于已有坐标的供应商可直接用 `--coords` / `--suppliers` 传入 lat/lon，跳过 Nominatim 查询。

**长期方案**: 考虑配置代理，或使用其他 geocoding 服务（如 Mapbox、Baidu）作为 fallback。

---

## 快速验证脚本

```bash
MAPS=~/.hermes/skills/productivity/maps/scripts/maps_client.py

# 验证脚本语法
python3 -c "import py_compile; py_compile.compile('$MAPS', doraise=True); print('Syntax OK')"

# 验证命令解析（不触发网络）
for cmd in supplier-geo logistics-cost supplier-clusters delivery-heatmap; do
  python3 $MAPS $cmd --help > /dev/null 2>&1 && echo "$cmd: OK" || echo "$cmd: FAIL"
done

# 测试聚类（纯本地计算，不触发网络）
python3 $MAPS supplier-clusters \
  --coords '[{"name":"A","lat":22.5,"lon":113.9},{"name":"B","lat":22.6,"lon":113.8}]' \
  --k 2 | python3 -c "import sys,json; d=json.load(sys.stdin); print('silhouette:', d['silhouette_score'])"
```

---

## 物流计价参数（内置，2025年参考值）

| 模式 | 计费方式 | 参数 |
|---|---|---|
| express（快递）| 首重1kg + 续重 | 首重 8元 + 5元/kg |
| truck（陆运）| 吨公里 | 0.35元/吨公里，最低50元 |
| air（空运）| 每公斤 | 18元/kg，最低120元 |

体积重计算公式: `(长×宽×高 cm) / 6000`

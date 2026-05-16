# 1688 Open Platform API — Response Examples

Found during browser exploration of https://open.1688.com (May 2026).

## alibaba.product.get — Full Response Structure

API: `com.alibaba.product:alibaba.product.get-1`

Request:
```json
{
  "productID": 584051070147,
  "webSite": "1688",
  "scene": ""
}
```

Response (truncated to relevant fields):
```json
{
  "productInfo": {
    "productID": 584051070147,
    "productType": "wholesale",
    "categoryID": 1048182,
    "attributes": [
      {
        "attributeID": 123456,
        "attributeName": "color",
        "valueID": 123456,
        "value": "grey",
        "isCustom": true
      }
    ],
    "groupID": [123],
    "status": "published",
    "subject": "高端气质OL韩版雪纺女装套头半高领长袖修身型蕾丝衫",
    "description": "...",
    "language": "ENGLISH",
    "periodOfValidity": 3650,
    "bizType": 1,
    "pictureAuth": false,
    "image": {
      "images": ["img/ibank/2014/766/624/1652426667_642119312.jpg"],
      "isWatermark": true,
      "isWatermarkFrame": true,
      "watermarkPosition": ""
    },
    "skuInfos": [
      {
        "attributes": [
          {
            "attributeID": 123,
            "attValueID": 123,
            "attributeValue": "",
            "customValueName": "",
            "skuImageUrl": "",
            "attributeDisplayName": "",
            "attributeName": "",
            "attrType": "1"
          }
        ],
        "cargoNumber": "货1001",
        "amountOnSale": 1000,
        "retailPrice": 10.0,
        "price": 10.0,
        "priceRange": [
          { "startQuantity": 123, "price": 1.23 }
        ],
        "skuCode": "774c",
        "skuId": 4469920756190,
        "specId": "774c48b20f3ef1ecdb1505e3d27c77f7",
        "consignPrice": 10.0,
        "takeSamplePrice": 10.0
      }
    ],
    "saleInfo": {
      "supportOnlineTrade": true,
      "mixWholeSale": true,
      "saleType": "normal",
      "priceAuth": true,
      "priceRanges": [{ "startQuantity": 123, "price": 1.23 }],
      "amountOnSale": 1.23,
      "unit": "",
      "minOrderQuantity": 123,
      "batchNumber": 123,
      "retailprice": 1.23,
      "sellunit": "",
      "quoteType": 123,
      "consignPrice": 1.23,
      "deliveryLimit": 5,
      "invReduceType": "1"
    },
    "shippingInfo": {
      "unitWeight": 121.0,
      "volume": 500,
      "handlingTime": 12,
      "freightTemplateID": 121133,
      "suttleWeight": 1001.0,
      "sendGoodsAddressText": "asda",
      "width": 30.0,
      "height": 20.0,
      "length": 10.0,
      "packageSize": "10x20x50",
      "sendGoodsAddressId": 124431,
      "offerSuttleWeight": 2.0,
      "offerWidth": 30.0,
      "offerHeight": 30.0,
      "offerLength": 30.0
    }
  },
  "bizGroupInfos": [],
  "createTime": "...",
  "lastUpdateTime": "..."
}
```

Also includes: `skuImages` array with `{ skuId, imageUrl }` mappings.

## alibaba.category.attribute.get — Full Response Structure

API: `com.alibaba.product:alibaba.category.attribute.get-1`

Response:
```json
{
  "success": true,
  "attributes": [
    {
      "attrID": 2489638,
      "name": "风格类型",
      "required": true,
      "fieldType": "enum",
      "isSKUAttribute": false,
      "attrValues": [
        { "attrValueID": 91043051, "name": "气质通勤" }
      ],
      "inputType": "1",
      "aspect": "0;",
      "isSpecPicAttr": false
    }
  ],
  "attributeLevelMapStr": {
    "2489638:9955810": "973",
    "1811:3289490": "20602,2917380,7001",
    "100000691:46874>7108:21958": "8243"
  }
}
```

### Cascading Attributes (attributeLevelMapStr)

Format: `parentAttrID:parentValueID>childAttrID:childValueID` → `grandchildAttrIDs`

Example from the docs:
For 连衣裙 class:
- `"100000691:46874>7108:21958": "8243"`
- 100000691 = 货源类别 (attrID), 46874 = 现货 (valueID)
- 7108 = 是否库存 (attrID), 21958 = 是 (valueID)
- 8243 = 库存类型 (attrID) — the cascaded attribute that must be filled

## API Doc URLs

- Main: https://open.1688.com
- Product APIs: https://open.1688.com/api/apidocdetail.htm?aopApiCategory=product_new
- Category APIs: https://open.1688.com/api/apidocdetail.htm?aopApiCategory=category_new
- Member APIs: https://open.1688.com/api/apidocdetail.htm?aopApiCategory=member
- Trade APIs: https://open.1688.com/api/apidocdetail.htm?aopApiCategory=trade_new
- Logistics APIs: https://open.1688.com/api/apidocdetail.htm?aopApiCategory=Logistics_NEW
- Photos API: https://open.1688.com/api/apidocdetail.htm?aopApiCategory=photobank_new

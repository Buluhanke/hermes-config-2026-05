# alibaba.category.attribute.get — Session-Extracted Spec

Extracted from https://open.1688.com/api/apidocdetail.htm?aopApiCategory=category_new&id=com.alibaba.product%3Aalibaba.category.attribute.get-1 (May 2026).

## API Info

- **名称**: 获取叶子类目属性
- **API**: alibaba.category.attribute.get
- **URL**: `POST https://gw.open.1688.com/openapi/param2/1/com.alibaba.product/alibaba.category.attribute.get/${APPKEY}`
- **所属解决方案**: 商品相关

## 系统级输入参数 (required for auth)

| 名称 | 类型 | 是否必须 | 描述 |
|------|------|---------|------|
| _aop_timestamp | String | 否 | 请求时间戳 |
| _aop_signature | String | 是 | 请求签名 |
| access_token | String | 是 | 用户授权令牌 |

## 应用级输入参数

| 名称 | 类型 | 是否必须 | 描述 | 示例值 |
|------|------|---------|------|--------|
| categoryID | Long | **是** | 类目ID | — |
| webSite | String | **是** | 站点信息，`"1688"`或`"alibaba"`（国际站） | — |
| scene | String | 否 | 场景值，可选值为空和 processing，默认为空 | `-` |

## 返回结果

| 名称 | 类型 | 描述 | 示例值 |
|------|------|------|--------|
| attributes | alibaba.category.AttributeInfo[] | 类目属性信息 | `[]` |
| levelAttrRelList | alibaba.category.PostLevelAttrRel[] | **(已废弃)** 类目属性级联关系，仅1688返回 | `[]` |
| attributeLevelMapStr | java.util.Map | 级联信息字符串，可强转成 map | `{"1811:3289490":"20602,2917380,7001"}` |
| errorMsg | String | 错误描述 | — |
| errorCode | String | 错误码 | — |
| success | Boolean | 是否成功 | `true` |

## 错误码

| 错误码 | 错误描述 | 解决方案 |
|--------|---------|---------|
| 500_2 | 数据准备中，请稍后重试。 | 数据正在后台加载，稍后重试，间隔时间建议1～3s |

## AttributeInfo 完整字段

```json
{
  "attrID": 2489638,        // Long - 属性ID
  "name": "风格类型",        // String - 属性名称
  "required": true,         // Boolean - 是否必填
  "fieldType": "enum",      // String - 字段类型 (enum/input/multiCheck)
  "isSKUAttribute": false,  // Boolean - 是否SKU规格属性（⭐ 核心）
  "attrValues": [           // Array - 可选值列表
    {
      "attrValueID": 91043051,
      "name": "气质通勤"
    }
  ],
  "inputType": "1",         // String - 输入类型 ("1"=下拉, "2"=文本)
  "aspect": "0;",           // String - 粒度信息
  "isSpecPicAttr": false    // Boolean - 是否规格图片属性
}
```

## attributeLevelMapStr 级联关系说明

格式：`parentAttrID:parentValueID>childAttrID:childValueID` → `grandchildAttrIDs`

示例（连衣裙类目）：
- `"100000691:46874>7108:21958": "8243"`
- 100000691 = 货源类别 (attrID)
- 46874 = 现货 (valueID)
- 7108 = 是否库存 (attrID)
- 21958 = 是 (valueID)
- 8243 = 库存类型 (attrID) — 级联后需要填写的属性

## 页面导航锚点

在浏览器里用下面锚点快速跳转：
- `#api-1` — 所属解决方案
- `#api-2` — 请求 URL
- `#api-3` — 系统级输入参数
- `#api-4` — 应用级输入参数
- `#api-5` — 返回结果
- `#api-6` — 返回结果示例

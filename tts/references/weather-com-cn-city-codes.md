# weather.com.cn City Codes for Common Chinese Cities

When SearXNG or other search backends fail (e.g. 502), use `web_extract` directly against China Weather Network for reliable weather data.

## URL Pattern

```
https://www.weather.com.cn/weather/{city_code}.shtml     # 7-day forecast
https://www.weather.com.cn/weather15d/{city_code}.shtml  # 15-day forecast
```

## Common Codes

| City | Code |
|------|------|
| 北京 | 101010100 |
| 上海 | 101020100 |
| 广州 | 101280101 |
| 深圳 | 101280601 |
| 杭州 | 101210101 |
| **义乌/金华** | **101210901** |
| 宁波 | 101210401 |
| 温州 | 101210701 |
| 南京 | 101190101 |
| 苏州 | 101190401 |
| 武汉 | 101200101 |
| 成都 | 101270101 |
| 重庆 | 101040100 |
| 西安 | 101110101 |

## Usage in Hermes

```python
web_extract(urls=["https://www.weather.com.cn/weather15d/101210901.shtml"])
```

Returns HTML content with day-by-day weather table. Extract: date, weather icon/text, high/low temperature, wind.

## Pitfalls

- The page includes city name at top, but the forecast covers the prefecture-level city (e.g. 金华 covers 义乌)
- 8-15 day forecast is labeled as lower confidence by the site
- Updates at ~11:30 and ~17:30 CST daily
- `web_extract` may return mixed content; look for table rows with date-weather-temp columns

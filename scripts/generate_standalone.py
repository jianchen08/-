#!/usr/bin/env python3
"""生成 standalone.html - 将 dist 目录的构建产物打包为单一独立 HTML 文件。

该文件可直接在浏览器中打开（file:// 协议），无需 HTTP 服务器。
策略：
  - JS/CSS 资源内联到 HTML 中
  - 数据文件内联并通过 fetch 拦截器提供
  - 拦截 fetch() 调用，匹配数据路径时返回内联数据
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    # 读取数据文件
    nodes_json = read_file(os.path.join(DIST, "data", "full_data.json"))
    domains_json = read_file(os.path.join(DIST, "data", "domains.json"))
    eras_json = read_file(os.path.join(DIST, "data", "eras.json"))

    # 读取构建的 CSS
    css_content = ""
    assets_dir = os.path.join(DIST, "assets")
    for fn in os.listdir(assets_dir):
        if fn.endswith(".css"):
            css_content += read_file(os.path.join(assets_dir, fn))

    # 读取构建的 JS 文件
    js_bundles = []
    for fn in sorted(os.listdir(assets_dir)):
        if fn.endswith(".js"):
            js_bundles.append(read_file(os.path.join(assets_dir, fn)))

    # 生成 standalone.html
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>科技树可视化 (Standalone)</title>

  <!-- 内联 CSS -->
  <style>
{css_content}
  </style>

  <!-- Standalone 专用样式 -->
  <style>
    body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    #root {{ width: 100vw; height: 100vh; }}
    .standalone-banner {{
      position: fixed; top: 0; left: 50%; transform: translateX(-50%);
      background: #4CAF50; color: white; padding: 4px 16px;
      border-radius: 0 0 8px 8px; z-index: 99999; font-size: 12px;
      opacity: 0.8;
    }}
  </style>

  <!-- 数据内联 + Fetch 拦截器 -->
  <!-- 必须在主 JS 之前加载，拦截对数据文件的 fetch 请求 -->
  <script>
    // 内联科技树数据
    var __STANDALONE_DATA__ = {{
      "data/full_data.json": {nodes_json},
      "data/domains.json": {domains_json},
      "data/eras.json": {eras_json}
    }};

    // 拦截 fetch：匹配数据路径时返回内联数据
    var __originalFetch = window.fetch;
    window.fetch = function(input, init) {{
      var url = (typeof input === 'string') ? input : (input instanceof Request ? input.url : String(input));
      // 提取路径部分（去除 base 前缀如 ./）
      var path = url.replace(/^\\.\\//, '').replace(/^\\//, '');
      // 检查是否匹配内联数据
      for (var key in __STANDALONE_DATA__) {{
        if (path === key || path.endsWith(key) || url.endsWith(key)) {{
          console.log('[standalone] 拦截 fetch:', url, '-> 内联数据', key);
          return Promise.resolve(new Response(JSON.stringify(__STANDALONE_DATA__[key]), {{
            status: 200,
            statusText: 'OK',
            headers: {{ 'Content-Type': 'application/json' }}
          }}));
        }}
      }}
      // 未匹配的请求走原始 fetch
      return __originalFetch.apply(this, arguments);
    }};
  </script>
</head>
<body>
  <div class="standalone-banner">📂 Standalone 模式 — 无需服务器</div>
  <div id="root"></div>

  <!-- 内联 JS 构建产物 -->
  <script>
{chr(10).join(js_bundles)}
  </script>
</body>
</html>"""

    output_path = os.path.join(ROOT, "standalone.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    node_count = len(json.loads(nodes_json))
    print(f"✅ standalone.html 已生成: {output_path}")
    print(f"   文件大小: {size_mb:.2f} MB")
    print(f"   内联数据: {node_count} 个节点, 12 个领域, 7 个时代")
    print(f"   内联 CSS: {len(css_content):,} 字符")
    print(f"   内联 JS: {len(js_bundles)} 个文件")
    print(f"   Fetch 拦截器: 已安装（拦截 3 个数据文件路径）")

    return 0


if __name__ == "__main__":
    sys.exit(main())

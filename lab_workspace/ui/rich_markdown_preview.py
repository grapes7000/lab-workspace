import json
import os
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor
from PySide6.QtWebEngineWidgets import QWebEngineView


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "markdown"


class _LocalOnlyInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        if info.requestUrl().scheme() not in {"about", "data", "file", "qrc"}:
            info.block(True)


class _ExternalLinkPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if navigation_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return url.scheme() in {"about", "data", "file", "qrc"}


class RichMarkdownPreview(QWebEngineView):
    _interceptor = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document_path = None
        profile = QWebEngineProfile.defaultProfile()
        if RichMarkdownPreview._interceptor is None:
            RichMarkdownPreview._interceptor = _LocalOnlyInterceptor(profile)
            profile.setUrlRequestInterceptor(RichMarkdownPreview._interceptor)
        self.setPage(_ExternalLinkPage(profile, self))
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)

    @staticmethod
    def _asset_url(name):
        return (ASSET_DIR / name).as_uri()

    @classmethod
    def html_for_markdown(cls, markdown):
        source = json.dumps(markdown).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
        assets = {name: cls._asset_url(name) for name in (
            "katex.min.css", "highlight-github.min.css", "markdown-it.min.js",
            "markdown-it-task-lists.min.js", "katex.min.js", "katex-auto-render.min.js",
            "highlight.min.js", "mermaid.min.js",
        )}
        return f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self' file: data:; img-src file: data:; style-src 'self' file: 'unsafe-inline'; script-src 'self' file: 'unsafe-inline'; font-src file: data:; connect-src 'none'\">
<link rel=\"stylesheet\" href=\"{assets['katex.min.css']}\"><link rel=\"stylesheet\" href=\"{assets['highlight-github.min.css']}\">
<style>body{{margin:12px;color:#292b2f;background:#fff;font:14px sans-serif;line-height:1.5}}img{{max-width:100%;height:auto}}pre{{padding:10px;background:#f5f5f6;border:1px solid #d3d4d7;border-radius:3px;overflow:auto}}code{{font-family:monospace}}table{{border-collapse:collapse}}th,td{{padding:6px 8px;border:1px solid #d3d4d7}}th{{background:#f0f0f1}}blockquote{{margin-left:0;padding-left:12px;border-left:3px solid #d3d4d7;color:#73767d}}.mermaid-error{{color:#9f2222;white-space:pre-wrap}}</style>
</head><body><main id=\"content\"></main>
<script src=\"{assets['markdown-it.min.js']}\"></script><script src=\"{assets['markdown-it-task-lists.min.js']}\"></script><script src=\"{assets['katex.min.js']}\"></script><script src=\"{assets['katex-auto-render.min.js']}\"></script><script src=\"{assets['highlight.min.js']}\"></script><script src=\"{assets['mermaid.min.js']}\"></script>
<script>
const source = {source};
const content = document.getElementById('content');
const renderer = window.markdownit({{html:false, linkify:true, typographer:false}}).use(window.markdownitTaskLists, {{enabled:true}});
content.innerHTML = renderer.render(source);
document.querySelectorAll('pre code').forEach((code) => {{
  if (!code.classList.contains('language-mermaid')) window.hljs.highlightElement(code);
}});
document.querySelectorAll('pre code.language-mermaid').forEach((code, index) => {{
  const diagram = document.createElement('pre');
  diagram.className = 'mermaid';
  diagram.id = `mermaid-${{index}}`;
  diagram.textContent = code.textContent;
  code.parentElement.replaceWith(diagram);
}});
window.mermaid.initialize({{startOnLoad:false, securityLevel:'strict', theme:'default'}});
window.mermaid.run({{nodes:document.querySelectorAll('.mermaid')}}).catch((error) => {{
  document.querySelectorAll('.mermaid').forEach((diagram) => {{
    const fallback = document.createElement('pre'); fallback.className = 'mermaid-error';
    fallback.textContent = `Mermaid rendering failed:\\n${{diagram.textContent}}`;
    diagram.replaceWith(fallback);
  }});
}}).finally(() => {{
  window.renderMathInElement(content, {{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}], throwOnError:false, ignoredTags:['script','noscript','style','textarea','pre','code']}});
}});
</script></body></html>"""

    def set_document_path(self, path):
        self.document_path = Path(path) if path else None

    def set_markdown(self, markdown, document_path=None):
        self.set_document_path(document_path)
        base = QUrl.fromLocalFile(str(self.document_path.parent) + os.sep) if self.document_path else QUrl.fromLocalFile(str(ASSET_DIR) + os.sep)
        self.setHtml(self.html_for_markdown(markdown), base)

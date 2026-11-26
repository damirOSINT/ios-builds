// A full-screen web view that runs an HTML5 game bundled in the app's www/
// folder. Files are served through the app:// scheme (as Cordova does on iOS)
// rather than file://, so the game's fetches and workers behave as on a web
// server.

import AVFoundation
import UIKit
import UniformTypeIdentifiers
import WebKit

final class BundleSchemeHandler: NSObject, WKURLSchemeHandler {
    private let root = Bundle.main.resourceURL!.appendingPathComponent("www")

    func webView(_ webView: WKWebView, start task: WKURLSchemeTask) {
        guard let url = task.request.url else { return }
        var path = url.path.removingPercentEncoding ?? url.path
        if path.isEmpty || path == "/" { path = "/index.html" }
        let file = root.appendingPathComponent(String(path.dropFirst())).standardizedFileURL
        guard file.path.hasPrefix(root.standardizedFileURL.path),
              let data = try? Data(contentsOf: file, options: .mappedIfSafe) else {
            task.didReceive(HTTPURLResponse(url: url, statusCode: 404, httpVersion: "HTTP/1.1", headerFields: nil)!)
            task.didFinish()
            return
        }
        let mime = UTType(filenameExtension: file.pathExtension)?.preferredMIMEType ?? "application/octet-stream"
        var headers = ["Content-Type": mime, "Accept-Ranges": "bytes", "Cache-Control": "no-cache"]
        var body = data
        var status = 200
        // Media elements ask for byte ranges.
        if let range = task.request.value(forHTTPHeaderField: "Range"),
           let spec = range.split(separator: "=").last {
            let parts = spec.split(separator: "-", omittingEmptySubsequences: false)
            let start = Int(parts.first ?? "") ?? 0
            let end = min(parts.count > 1 ? Int(parts[1]) ?? data.count - 1 : data.count - 1, data.count - 1)
            if start <= end {
                body = data.subdata(in: start..<(end + 1))
                headers["Content-Range"] = "bytes \(start)-\(end)/\(data.count)"
                status = 206
            }
        }
        headers["Content-Length"] = String(body.count)
        task.didReceive(HTTPURLResponse(url: url, statusCode: status, httpVersion: "HTTP/1.1", headerFields: headers)!)
        task.didReceive(body)
        task.didFinish()
    }

    func webView(_ webView: WKWebView, stop task: WKURLSchemeTask) {}
}

final class GameViewController: UIViewController {
    private var webView: WKWebView!

    override func loadView() {
        let config = WKWebViewConfiguration()
        config.setURLSchemeHandler(BundleSchemeHandler(), forURLScheme: "app")
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []
        // Errors the page throws are shown over it, since there's no
        // console to read on the phone.
        config.userContentController.addUserScript(WKUserScript(source: """
            (function () {
                function show(text) {
                    var box = document.getElementById("__errors");
                    if (!box) {
                        box = document.createElement("pre");
                        box.id = "__errors";
                        box.style.cssText = "position:fixed;left:0;right:0;bottom:0;max-height:45%;overflow:auto;margin:0;padding:8px;background:rgba(0,0,0,.85);color:#ff6b6b;font:12px monospace;z-index:2147483647;white-space:pre-wrap";
                        (document.body || document.documentElement).appendChild(box);
                    }
                    box.textContent += text + "\n";
                }
                window.addEventListener("error", function (e) {
                    show("Error: " + e.message + " (" + (e.filename || "") + ":" + (e.lineno || "") + ")");
                });
                window.addEventListener("unhandledrejection", function (e) {
                    show("Unhandled: " + (e.reason && (e.reason.stack || e.reason.message) || e.reason));
                });
            })();
            """, injectionTime: .atDocumentStart, forMainFrameOnly: true))
        webView = WKWebView(frame: .zero, configuration: config)
        webView.isOpaque = false
        webView.backgroundColor = .black
        webView.scrollView.isScrollEnabled = false
        webView.scrollView.bounces = false
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        view = webView
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        webView.load(URLRequest(url: URL(string: "app://localhost/index.html")!))
    }

    override var prefersStatusBarHidden: Bool { true }
    override var prefersHomeIndicatorAutoHidden: Bool { true }
    // Landscape unless Info.plist also lists portrait (games built with orient: all).
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask {
        let list = Bundle.main.object(forInfoDictionaryKey: "UISupportedInterfaceOrientations") as? [String] ?? []
        return list.contains("UIInterfaceOrientationPortrait") ? .allButUpsideDown : .landscape
    }
}

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        try? AVAudioSession.sharedInstance().setCategory(.playback)
        window = UIWindow(frame: UIScreen.main.bounds)
        window?.rootViewController = GameViewController()
        window?.makeKeyAndVisible()
        return true
    }
}

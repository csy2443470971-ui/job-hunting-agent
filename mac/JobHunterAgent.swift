// Job Hunter Agent for macOS: one window on the local dashboard, with its own Dock icon.
//
// It starts the dashboard server if it isn't running (and stops it on quit if it started it), shows it in a
// WKWebView, and stays a normal app: opening it again, or a jobhunter:// link, brings the same window forward.
// What a browser gave the dashboard is provided here too: file pickers, alert/confirm/prompt, links that leave
// the dashboard open in the default browser, and voice input (the page's SpeechRecognition is answered by
// macOS speech recognition). Built by mac/build.sh, which fills in the repo and Python paths.

import AVFoundation
import Cocoa
import Speech
import WebKit

let info = Bundle.main.infoDictionary ?? [:]
let repo = info["JHARepo"] as? String ?? FileManager.default.currentDirectoryPath
let python = info["JHAPython"] as? String ?? "/usr/bin/python3"
let port = info["JHAPort"] as? String ?? "8765"
let home = URL(string: "http://127.0.0.1:\(port)/")!

func jsString(_ s: String) -> String {
    let data = try! JSONSerialization.data(withJSONObject: [s])
    return String(String(data: data, encoding: .utf8)!.dropFirst().dropLast())
}

// MARK: - the dashboard server

final class Server {
    private var process: Process?

    func isUp(_ done: @escaping (Bool) -> Void) {
        var req = URLRequest(url: home.appendingPathComponent("api/config")); req.timeoutInterval = 1
        URLSession.shared.dataTask(with: req) { _, resp, _ in
            done((resp as? HTTPURLResponse)?.statusCode == 200)
        }.resume()
    }

    /// Calls back on the main queue once the dashboard answers (starting it first if needed).
    func ensure(_ ready: @escaping (Bool) -> Void) {
        isUp { up in
            if up { return DispatchQueue.main.async { ready(true) } }
            DispatchQueue.main.async {
                self.start()
                self.wait(tries: 80, ready)
            }
        }
    }

    private func start() {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: python)
        p.arguments = ["-m", "dashboard.app"]
        p.currentDirectoryURL = URL(fileURLWithPath: repo)
        var env = ProcessInfo.processInfo.environment
        env["JHA_PORT"] = port
        env["PATH"] = "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:" + (env["PATH"] ?? "")
        p.environment = env
        let logURL = URL(fileURLWithPath: repo).appendingPathComponent("data/app.log")
        try? FileManager.default.createDirectory(at: logURL.deletingLastPathComponent(), withIntermediateDirectories: true)
        if !FileManager.default.fileExists(atPath: logURL.path) { FileManager.default.createFile(atPath: logURL.path, contents: nil) }
        if let log = try? FileHandle(forWritingTo: logURL) { log.seekToEndOfFile(); p.standardOutput = log; p.standardError = log }
        do { try p.run(); process = p } catch { NSLog("could not start the dashboard: \(error)") }
    }

    private func wait(tries: Int, _ ready: @escaping (Bool) -> Void) {
        isUp { up in
            DispatchQueue.main.async {
                if up { ready(true) }
                else if tries <= 0 { ready(false) }
                else { DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { self.wait(tries: tries - 1, ready) } }
            }
        }
    }

    /// Only the server this app started is stopped; one started elsewhere keeps running.
    func stop() { if let p = process, p.isRunning { p.terminate() } }
}

// MARK: - voice input for the page

final class Speech: NSObject, WKScriptMessageHandler {
    weak var web: WKWebView?
    private let engine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private var active = false

    static let shim = """
    (() => {
      class SR {
        constructor() { this.continuous = false; this.interimResults = false; this.lang = 'en-US'; }
        start() { SR.cur = this; webkit.messageHandlers.jhaSpeech.postMessage({cmd: 'start', lang: this.lang}); }
        stop() { webkit.messageHandlers.jhaSpeech.postMessage({cmd: 'stop'}); }
        abort() { this.stop(); }
      }
      window.__jhaSpeech = {
        result(t) { const s = SR.cur; s && s.onresult && s.onresult({results: [[{transcript: t}]]}); },
        end() { const s = SR.cur; SR.cur = null; s && s.onend && s.onend(); },
        error(e) { const s = SR.cur; s && s.onerror && s.onerror({error: e}); if (e === 'not-allowed') alert('Voice input needs microphone and speech recognition access: System Settings → Privacy & Security.'); this.end(); },
      };
      window.SpeechRecognition = window.webkitSpeechRecognition = SR;
    })();
    """

    func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage) {
        guard let d = m.body as? [String: Any], let cmd = d["cmd"] as? String else { return }
        if cmd == "start" { start(lang: d["lang"] as? String ?? "en-US") } else { stop() }
    }

    private func js(_ s: String) { DispatchQueue.main.async { self.web?.evaluateJavaScript(s) } }

    private func start(lang: String) {
        SFSpeechRecognizer.requestAuthorization { status in
            guard status == .authorized else { return self.js("__jhaSpeech.error('not-allowed')") }
            AVCaptureDevice.requestAccess(for: .audio) { ok in
                guard ok else { return self.js("__jhaSpeech.error('not-allowed')") }
                DispatchQueue.main.async { self.begin(lang: lang) }
            }
        }
    }

    private func begin(lang: String) {
        stop(quiet: true)
        guard let rec = SFSpeechRecognizer(locale: Locale(identifier: lang)) ?? SFSpeechRecognizer(), rec.isAvailable else {
            return js("__jhaSpeech.error('unavailable')")
        }
        let req = SFSpeechAudioBufferRecognitionRequest(); req.shouldReportPartialResults = true
        let input = engine.inputNode
        input.installTap(onBus: 0, bufferSize: 1024, format: input.outputFormat(forBus: 0)) { buf, _ in req.append(buf) }
        engine.prepare()
        do { try engine.start() } catch { input.removeTap(onBus: 0); return js("__jhaSpeech.error('audio-capture')") }
        request = req; active = true
        task = rec.recognitionTask(with: req) { [weak self] res, err in
            guard let self = self, self.active else { return }
            if let res = res { self.js("__jhaSpeech.result(\(jsString(res.bestTranscription.formattedString)))") }
            if err != nil || res?.isFinal == true { DispatchQueue.main.async { self.stop() } }
        }
    }

    func stop(quiet: Bool = false) {
        let was = active
        active = false
        if engine.isRunning { engine.stop(); engine.inputNode.removeTap(onBus: 0) }
        request?.endAudio(); request = nil
        task?.cancel(); task = nil
        if was && !quiet { js("__jhaSpeech.end()") }
    }
}

// MARK: - the window

final class AppDelegate: NSObject, NSApplicationDelegate, WKUIDelegate, WKNavigationDelegate {
    let server = Server()
    let speech = Speech()
    var window: NSWindow!
    var web: WKWebView!

    func applicationWillFinishLaunching(_ n: Notification) {
        NSAppleEventManager.shared().setEventHandler(self, andSelector: #selector(openURL(_:reply:)),
                                                     forEventClass: AEEventClass(kInternetEventClass), andEventID: AEEventID(kAEGetURL))
    }

    func applicationDidFinishLaunching(_ n: Notification) {
        buildMenu()
        let conf = WKWebViewConfiguration()
        conf.userContentController.addUserScript(WKUserScript(source: Speech.shim, injectionTime: .atDocumentStart, forMainFrameOnly: true))
        conf.userContentController.add(speech, name: "jhaSpeech")
        conf.preferences.setValue(true, forKey: "developerExtrasEnabled")
        web = WKWebView(frame: .zero, configuration: conf)
        web.uiDelegate = self; web.navigationDelegate = self
        web.allowsBackForwardNavigationGestures = false
        speech.web = web
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1440, height: 900),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView], backing: .buffered, defer: false)
        window.title = "Job Hunter Agent"
        window.titlebarAppearsTransparent = true
        window.minSize = NSSize(width: 760, height: 520)
        window.contentView = web
        window.center()
        window.setFrameAutosaveName("JobHunterAgentMain")
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        web.loadHTMLString("<body style=\"margin:0;height:100vh;display:flex;align-items:center;justify-content:center;font:15px -apple-system;color:#78716C;background:#FAF8F5\">Starting your agent…</body>", baseURL: nil)
        server.ensure { ok in
            if ok { self.web.load(URLRequest(url: home)) }
            else { self.web.loadHTMLString("<body style=\"font:15px -apple-system;padding:40px;color:#44403C\">The dashboard didn't start. See data/app.log in the project folder.</body>", baseURL: nil) }
        }
    }

    // one app, one window: opening it again brings this window back
    func applicationShouldHandleReopen(_ s: NSApplication, hasVisibleWindows: Bool) -> Bool { window.makeKeyAndOrderFront(nil); return true }
    func applicationShouldTerminateAfterLastWindowClosed(_ s: NSApplication) -> Bool { true }
    func applicationWillTerminate(_ n: Notification) { speech.stop(quiet: true); server.stop() }
    @objc func openURL(_ e: NSAppleEventDescriptor, reply: NSAppleEventDescriptor) { window?.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true) }

    // links that leave the dashboard open in the default browser
    func webView(_ w: WKWebView, decidePolicyFor a: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let u = a.request.url, a.navigationType == .linkActivated, u.host != home.host || u.port != home.port {
            NSWorkspace.shared.open(u); return decisionHandler(.cancel)
        }
        decisionHandler(.allow)
    }
    func webView(_ w: WKWebView, createWebViewWith c: WKWebViewConfiguration, for a: WKNavigationAction, windowFeatures f: WKWindowFeatures) -> WKWebView? {
        if let u = a.request.url { NSWorkspace.shared.open(u) }
        return nil
    }

    // what a browser would show
    func webView(_ w: WKWebView, runJavaScriptAlertPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let a = NSAlert(); a.messageText = m; a.addButton(withTitle: "OK"); a.beginSheetModal(for: window) { _ in completionHandler() }
    }
    func webView(_ w: WKWebView, runJavaScriptConfirmPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let a = NSAlert(); a.messageText = m; a.addButton(withTitle: "OK"); a.addButton(withTitle: "Cancel")
        a.beginSheetModal(for: window) { r in completionHandler(r == .alertFirstButtonReturn) }
    }
    func webView(_ w: WKWebView, runJavaScriptTextInputPanelWithPrompt p: String, defaultText d: String?, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping (String?) -> Void) {
        let a = NSAlert(); a.messageText = p; a.addButton(withTitle: "OK"); a.addButton(withTitle: "Cancel")
        let field = NSTextField(frame: NSRect(x: 0, y: 0, width: 320, height: 24)); field.stringValue = d ?? ""; a.accessoryView = field
        a.window.initialFirstResponder = field
        a.beginSheetModal(for: window) { r in completionHandler(r == .alertFirstButtonReturn ? field.stringValue : nil) }
    }
    func webView(_ w: WKWebView, runOpenPanelWith p: WKOpenPanelParameters, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        let o = NSOpenPanel(); o.allowsMultipleSelection = p.allowsMultipleSelection; o.canChooseDirectories = false
        o.beginSheetModal(for: window) { r in completionHandler(r == .OK ? o.urls : nil) }
    }

    @objc func reload(_ s: Any?) { web.reload() }

    private func buildMenu() {
        let main = NSMenu()
        let appItem = NSMenuItem(); main.addItem(appItem)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "About Job Hunter Agent", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Hide Job Hunter Agent", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(withTitle: "Quit Job Hunter Agent", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        let editItem = NSMenuItem(); main.addItem(editItem)
        let edit = NSMenu(title: "Edit")
        edit.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
        edit.addItem(withTitle: "Redo", action: Selector(("redo:")), keyEquivalent: "Z")
        edit.addItem(.separator())
        edit.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        edit.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        edit.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        edit.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = edit
        let viewItem = NSMenuItem(); main.addItem(viewItem)
        let view = NSMenu(title: "View")
        view.addItem(withTitle: "Reload", action: #selector(reload(_:)), keyEquivalent: "r")
        viewItem.submenu = view
        let winItem = NSMenuItem(); main.addItem(winItem)
        let win = NSMenu(title: "Window")
        win.addItem(withTitle: "Minimize", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        win.addItem(withTitle: "Close", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        winItem.submenu = win
        NSApp.mainMenu = main
        NSApp.windowsMenu = win
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()

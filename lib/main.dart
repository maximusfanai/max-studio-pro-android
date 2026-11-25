import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Color(0xFF050510),
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF050510),
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  runApp(const MaxStudioProApp());
}

class MaxStudioProApp extends StatelessWidget {
  const MaxStudioProApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MAX Studio Pro',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF050510),
      ),
      home: const SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _fadeAnim = CurvedAnimation(parent: _controller, curve: Curves.easeIn);
    _controller.forward();

    Future.delayed(const Duration(milliseconds: 2200), () {
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const MaxStudioWebView()),
      );
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050510),
      body: FadeTransition(
        opacity: _fadeAnim,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Image.asset(
                'assets/logo.png',
                width: 140,
                height: 140,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const Icon(
                  Icons.graphic_eq,
                  size: 84,
                  color: Color(0xFF00E5FF),
                ),
              ),
              const SizedBox(height: 18),
              const Text(
                'MAX Studio Pro',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  letterSpacing: 0.6,
                ),
              ),
              const SizedBox(height: 16),
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2.4,
                  color: Color(0xFFB33CFF),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class MaxStudioWebView extends StatefulWidget {
  const MaxStudioWebView({super.key});

  @override
  State<MaxStudioWebView> createState() => _MaxStudioWebViewState();
}

class _MaxStudioWebViewState extends State<MaxStudioWebView> {
  static const String _appUrl =
      'https://max-studio-pro-xfuruhajrcfkwzwfrwlif9.streamlit.app/';

  InAppWebViewController? _webViewController;
  double _progress = 0.0;
  bool _hasError = false;
  String _errorMessage = '';

  @override
  void initState() {
    super.initState();
    _requestPermissions();
  }

  Future<void> _requestPermissions() async {
    try {
      await [
        Permission.storage,
        Permission.audio,
        Permission.microphone,
      ].request();
    } catch (_) {}
  }

  Future<String> _getDownloadDirectoryPath() async {
    if (Platform.isAndroid) {
      final publicDownloads = Directory('/storage/emulated/0/Download');
      if (await publicDownloads.exists()) {
        return publicDownloads.path;
      }
    }
    final dir = await getApplicationDocumentsDirectory();
    return dir.path;
  }

  Future<void> _saveBase64File(
    String base64Data,
    String fileName,
  ) async {
    try {
      final cleanBase64 = base64Data.contains(',')
          ? base64Data.split(',').last
          : base64Data;
      final bytes = base64Decode(cleanBase64);
      final folderPath = await _getDownloadDirectoryPath();
      final safeName = fileName.trim().isEmpty
          ? 'max_studio_export_${DateTime.now().millisecondsSinceEpoch}.bin'
          : fileName.trim();
      final file = File('$folderPath/$safeName');
      await file.writeAsBytes(bytes);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Saved: $safeName'),
          backgroundColor: const Color(0xFF1A1438),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Download failed: $e'),
          backgroundColor: Colors.redAccent,
        ),
      );
    }
  }

  void _registerBlobDownloadHandler(InAppWebViewController controller) {
    controller.addJavaScriptHandler(
      handlerName: 'blobDownloader',
      callback: (args) async {
        if (args.isNotEmpty) {
          final raw = args[0].toString();
          final fileName = args.length > 1 && args[1] != null
              ? args[1].toString()
              : 'download.bin';
          await _saveBase64File(raw, fileName);
        }
        return {'status': 'ok'};
      },
    );
  }

  Future<bool> _onWillPop() async {
    if (_webViewController != null && await _webViewController!.canGoBack()) {
      await _webViewController!.goBack();
      return false;
    }
    return true;
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: _onWillPop,
      child: Scaffold(
        backgroundColor: const Color(0xFF050510),
        body: SafeArea(
          child: Stack(
            children: [
              if (!_hasError)
                InAppWebView(
                  initialUrlRequest: URLRequest(url: WebUri(_appUrl)),
                  initialSettings: InAppWebViewSettings(
                    javaScriptEnabled: true,
                    domStorageEnabled: true,
                    databaseEnabled: true,
                    thirdPartyCookiesEnabled: true,
                    supportMultipleWindows: true,
                    javaScriptCanOpenWindowsAutomatically: true,
                    mediaPlaybackRequiresUserGesture: false,
                    allowFileAccess: true,
                    allowContentAccess: true,
                    useHybridComposition: true,
                    transparentBackground: true,
                  ),
                  onWebViewCreated: (controller) {
                    _webViewController = controller;
                    _registerBlobDownloadHandler(controller);
                  },
                  onLoadStart: (controller, url) {
                    setState(() {
                      _hasError = false;
                      _errorMessage = '';
                    });
                  },
                  onProgressChanged: (controller, progress) {
                    setState(() {
                      _progress = progress / 100.0;
                    });
                  },
                  onLoadStop: (controller, url) async {
                    setState(() {
                      _progress = 1.0;
                    });
                    await controller.evaluateJavascript(source: '''
                      (function() {
                        if (window.__maxBlobHookInstalled) return;
                        window.__maxBlobHookInstalled = true;
                        const origClick = HTMLAnchorElement.prototype.click;
                        HTMLAnchorElement.prototype.click = function() {
                          const href = this.getAttribute('href') || '';
                          const fname = this.getAttribute('download') || 'audio_export';
                          if (href.startsWith('blob:') && window.flutter_inappwebview) {
                            fetch(href)
                              .then(r => r.blob())
                              .then(blob => new Promise((resolve) => {
                                const reader = new FileReader();
                                reader.onloadend = () => resolve(reader.result);
                                reader.readAsDataURL(blob);
                              }))
                              .then(dataUrl => {
                                window.flutter_inappwebview.callHandler('blobDownloader', dataUrl, fname);
                              })
                              .catch(() => origClick.call(this));
                            return;
                          }
                          return origClick.call(this);
                        };
                      })();
                    ''');
                  },
                  onCreateWindow: (controller, createWindowAction) async {
                    final targetUrl = createWindowAction.request.url;
                    if (targetUrl != null) {
                      await controller.loadUrl(
                        urlRequest: URLRequest(url: targetUrl),
                      );
                    }
                    return true;
                  },
                  onReceivedError: (controller, request, error) {
                    if (request.isForMainFrame ?? true) {
                      setState(() {
                        _hasError = true;
                        _errorMessage = error.description;
                      });
                    }
                  },
                  onDownloadStartRequest: (controller, downloadStartRequest) async {
                    final url = downloadStartRequest.url.toString();
                    final suggestedName =
                        downloadStartRequest.suggestedFilename ?? 'stem_output';
                    if (url.startsWith('data:')) {
                      await _saveBase64File(url, suggestedName);
                    }
                  },
                ),
              if (_progress < 1.0 && !_hasError)
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
                  child: LinearProgressIndicator(
                    value: _progress > 0 ? _progress : null,
                    minHeight: 3,
                    backgroundColor: Colors.transparent,
                    color: const Color(0xFF00E5FF),
                  ),
                ),
              if (_hasError)
                Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.wifi_off,
                          size: 52,
                          color: Color(0xFF00E5FF),
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Connection Error',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _errorMessage.isEmpty
                              ? 'Server harh chhung emaw internet check rawh.'
                              : _errorMessage,
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Colors.white70),
                        ),
                        const SizedBox(height: 18),
                        ElevatedButton.icon(
                          onPressed: () {
                            setState(() {
                              _hasError = false;
                              _progress = 0.0;
                            });
                            _webViewController?.loadUrl(
                              urlRequest: URLRequest(url: WebUri(_appUrl)),
                            );
                          },
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

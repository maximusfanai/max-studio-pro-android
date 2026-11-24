import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';

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
        MaterialPageRoute(builder: (_) => const StudioWebViewScreen()),
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
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(0, -0.15),
            radius: 1.0,
            colors: [
              Color(0xFF1E0B42),
              Color(0xFF090718),
              Color(0xFF050510),
            ],
          ),
        ),
        child: FadeTransition(
          opacity: _fadeAnim,
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 118,
                  height: 118,
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        Color(0xFF00F0FF),
                        Color(0xFF8A2BE2),
                        Color(0xFFFF2E93),
                      ],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF00F0FF).withOpacity(0.45),
                        blurRadius: 26,
                        spreadRadius: 3,
                      ),
                      BoxShadow(
                        color: const Color(0xFFFF2E93).withOpacity(0.45),
                        blurRadius: 32,
                        spreadRadius: 4,
                      ),
                    ],
                  ),
                  child: ClipOval(
                    child: Container(
                      color: const Color(0xFF080616),
                      child: Image.asset(
                        'theme.png',
                        fit: BoxFit.cover,
                        errorBuilder: (context, error, stackTrace) {
                          return const Icon(
                            Icons.graphic_eq_rounded,
                            size: 54,
                            color: Color(0xFF00F0FF),
                          );
                        },
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                ShaderMask(
                  shaderCallback: (bounds) => const LinearGradient(
                    colors: [
                      Color(0xFF00F0FF),
                      Color(0xFF9D4EDD),
                      Color(0xFFFF2E93),
                    ],
                  ).createShader(
                    Rect.fromLTWH(0, 0, bounds.width, bounds.height),
                  ),
                  child: const Text(
                    'MAX STUDIO PRO',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 30,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.6,
                      color: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: const Color(0xFF00F0FF).withOpacity(0.5),
                    ),
                    color: const Color(0xFF00F0FF).withOpacity(0.1),
                  ),
                  child: const Text(
                    'AI Stem Splitter',
                    style: TextStyle(
                      fontSize: 14,
                      color: Color(0xFF00F0FF),
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class StudioWebViewScreen extends StatefulWidget {
  const StudioWebViewScreen({super.key});

  @override
  State<StudioWebViewScreen> createState() => _StudioWebViewScreenState();
}

class _StudioWebViewScreenState extends State<StudioWebViewScreen>
    with WidgetsBindingObserver {
  InAppWebViewController? _webController;
  double _progress = 0;

  static const String _appUrl = 'https://max-studio-pro.streamlit.app/';

  static const String _chromeUserAgent =
      'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _requestPermissions();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
      CookieManager.instance().flush();
    }
  }

  Future<void> _requestPermissions() async {
    await [Permission.storage, Permission.audio].request();
  }

  Future<void> _saveBase64File(
    String base64Data,
    String filename,
    String mimeType,
  ) async {
    try {
      final cleanBase64 = base64Data.contains(',')
          ? base64Data.split(',').last
          : base64Data;
      final bytes = base64Decode(cleanBase64);

      Directory? targetDir;
      if (Platform.isAndroid) {
        targetDir = Directory('/storage/emulated/0/Download');
        if (!await targetDir.exists()) {
          targetDir = await getExternalStorageDirectory();
        }
      } else {
        targetDir = await getApplicationDocumentsDirectory();
      }

      final safeName = filename.isEmpty
          ? 'stem_${DateTime.now().millisecondsSinceEpoch}.mp3'
          : filename;
      final file = File('${targetDir!.path}/$safeName');
      await file.writeAsBytes(bytes);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: const Color(0xFF1A0E38),
          content: Text(
            'Saved to Downloads: $safeName',
            style: const TextStyle(color: Colors.white),
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Download failed: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        if (_webController != null && await _webController!.canGoBack()) {
          await _webController!.goBack();
        }
      },
      child: Scaffold(
        backgroundColor: const Color(0xFF050510),
        body: SafeArea(
          child: Stack(
            children: [
              InAppWebView(
                initialUrlRequest: URLRequest(url: WebUri(_appUrl)),
                initialSettings: InAppWebViewSettings(
                  userAgent: _chromeUserAgent,
                  javaScriptEnabled: true,
                  javaScriptCanOpenWindowsAutomatically: true,
                  supportMultipleWindows: true,
                  domStorageEnabled: true,
                  databaseEnabled: true,
                  cacheEnabled: true,
                  clearCache: false,
                  incognito: false,
                  thirdPartyCookiesEnabled: true,
                  sharedCookiesEnabled: true,
                  allowFileAccess: true,
                  allowContentAccess: true,
                  useOnDownloadStart: true,
                  useShouldOverrideUrlLoading: true,
                  mediaPlaybackRequiresUserGesture: false,
                  supportZoom: false,
                  transparentBackground: true,
                ),
                onWebViewCreated: (controller) {
                  _webController = controller;
                  controller.addJavaScriptHandler(
                    handlerName: 'blobDownloader',
                    callback: (args) async {
                      if (args.length >= 2) {
                        await _saveBase64File(
                          args[0].toString(),
                          args[1].toString(),
                          args.length > 2 ? args[2].toString() : 'audio/mpeg',
                        );
                      }
                    },
                  );
                },
                onLoadStop: (controller, url) async {
                  await CookieManager.instance().flush();
                },
                shouldOverrideUrlLoading: (controller, navigationAction) async {
                  return NavigationActionPolicy.ALLOW;
                },
                onCreateWindow: (controller, createWindowAction) async {
                  final popupUrl = createWindowAction.request.url;
                  if (popupUrl != null) {
                    await controller.loadUrl(
                      urlRequest: URLRequest(url: popupUrl),
                    );
                  }
                  return false;
                },
                onProgressChanged: (controller, progress) {
                  setState(() => _progress = progress / 100.0);
                },
                onDownloadStartRequest: (controller, request) async {
                  final url = request.url.toString();
                  final filename =
                      request.suggestedFilename ?? 'max_stem_track.mp3';
                  if (url.startsWith('blob:') || url.startsWith('data:')) {
                    await controller.evaluateJavascript(
                      source:
                          '''
                      (async function() {
                        const res = await fetch("$url");
                        const blob = await res.blob();
                        const reader = new FileReader();
                        reader.onloadend = function() {
                          window.flutter_inappwebview.callHandler('blobDownloader', reader.result, "$filename", blob.type);
                        };
                        reader.readAsDataURL(blob);
                      })();
                    ''',
                    );
                  }
                },
              ),
              if (_progress < 1.0)
                LinearProgressIndicator(
                  value: _progress,
                  minHeight: 3,
                  backgroundColor: const Color(0xFF0B0920),
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    Color(0xFFB33CFF),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

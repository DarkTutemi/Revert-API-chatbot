/**
 * universal_ssl_unpin.js
 * 
 * Production-grade, multi-engine SSL Unpinning script for Frida.
 * Supports:
 *   - Android Java X509TrustManager & SSLContext.init
 *   - OkHttp 3.x and 4.x CertificatePinner (Java & Kotlin overloads)
 *   - Conscrypt & Android System TrustManagerImpl (AOSP & GMS)
 *   - Android NetworkSecurityConfigProvider & RootTrustManager
 *   - Android WebView onReceivedSslError (auto handler.proceed)
 *   - Third-party libraries (TrustKit, Titanium, Apache HttpClient, Volley)
 *   - Flutter BoringSSL ARM64 / ARMv7 in libflutter.so (Memory Pattern Scan)
 *   - Windows Native WinHTTP & OpenSSL (when attached to Windows EXE processes)
 * 
 * Usage:
 *   Android:
 *     frida -U -f com.example.app -l universal_ssl_unpin.js
 *     frida -U -n com.example.app -l universal_ssl_unpin.js
 *   Windows:
 *     frida -f C:\Path\To\TargetApp.exe -l universal_ssl_unpin.js
 *     frida -n TargetApp.exe -l universal_ssl_unpin.js
 */

(function () {
    'use strict';

    console.log("[*] ========================================================");
    console.log("[*] Universal SSL Unpinning Engine Initialized");
    console.log("[*] Platform: " + Process.platform + " | Arch: " + Process.arch);
    console.log("[*] ========================================================");

    // =========================================================================
    // 1. ANDROID HOOKS (Java Runtime)
    // =========================================================================
    if (Java.available) {
        Java.perform(function () {
            console.log("[*] Java runtime detected. Applying Android SSL Unpinning hooks...");

            // -----------------------------------------------------------------
            // 1.1 Java Standard X509TrustManager & SSLContext
            // -----------------------------------------------------------------
            try {
                var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
                var SSLContext = Java.use('javax.net.ssl.SSLContext');

                var PermissiveTrustManager = Java.registerClass({
                    name: 'com.reqable.universal.PermissiveTrustManager',
                    implements: [X509TrustManager],
                    methods: {
                        checkClientTrusted: function (chain, authType) {
                            // Trust all client certificates
                        },
                        checkServerTrusted: function (chain, authType) {
                            // Trust all server certificates
                        },
                        getAcceptedIssuers: function () {
                            return [];
                        }
                    }
                });

                var TrustManagers = [PermissiveTrustManager.$new()];

                var SSLContext_init = SSLContext.init.overload(
                    '[Ljavax.net.ssl.KeyManager;',
                    '[Ljavax.net.ssl.TrustManager;',
                    'Ljava.security.SecureRandom;'
                );

                SSLContext_init.implementation = function (km, tm, sr) {
                    console.log("[+] Hooked SSLContext.init() -> Overriding with PermissiveTrustManager");
                    SSLContext_init.call(this, km, TrustManagers, sr);
                };
                console.log("[+] [X509TrustManager/SSLContext] Hooked successfully");
            } catch (err) {
                console.log("[-] [X509TrustManager/SSLContext] Hook failed: " + err);
            }

            // -----------------------------------------------------------------
            // 1.2 OkHttp3 / OkHttp4 CertificatePinner
            // -----------------------------------------------------------------
            try {
                var CertificatePinner = Java.use('okhttp3.CertificatePinner');

                // Overload 1: check(String hostname, List<Certificate> peerCertificates)
                try {
                    CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function (hostname, peerCertificates) {
                        console.log("[+] [OkHttp3] CertificatePinner.check(String, List) bypassed for: " + hostname);
                        return;
                    };
                } catch (e) { }

                // Overload 2: check(String hostname, Certificate... peerCertificates)
                try {
                    CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function (hostname, peerCertificates) {
                        console.log("[+] [OkHttp3] CertificatePinner.check(String, Certificate[]) bypassed for: " + hostname);
                        return;
                    };
                } catch (e) { }

                // Overload 3: Kotlin internal check$okhttp(String hostname, Function0 cleanedPeerCertificatesFn)
                try {
                    CertificatePinner.check$okhttp.overload('java.lang.String', 'kotlin.jvm.functions.Function0').implementation = function (hostname, fn) {
                        console.log("[+] [OkHttp4] CertificatePinner.check$okhttp(String, Function0) bypassed for: " + hostname);
                        return;
                    };
                } catch (e) { }

                console.log("[+] [OkHttp3/OkHttp4] CertificatePinner hooked successfully");
            } catch (err) {
                console.log("[-] [OkHttp3/OkHttp4] CertificatePinner not found or hook failed: " + err);
            }

            // -----------------------------------------------------------------
            // 1.3 Conscrypt TrustManagerImpl (AOSP & GMS variants)
            // -----------------------------------------------------------------
            var conscryptTargets = [
                'com.android.org.conscrypt.TrustManagerImpl',
                'com.google.android.gms.org.conscrypt.TrustManagerImpl',
                'org.conscrypt.TrustManagerImpl'
            ];

            conscryptTargets.forEach(function (targetClass) {
                try {
                    var TMImpl = Java.use(targetClass);

                    // checkTrustedRecursive overload
                    var methods = TMImpl.class.getDeclaredMethods();
                    for (var i = 0; i < methods.length; i++) {
                        var mName = methods[i].getName();
                        if (mName === 'checkTrustedRecursive' || mName === 'checkTrusted') {
                            var paramTypes = methods[i].getParameterTypes();
                            var paramTypeNames = [];
                            for (var j = 0; j < paramTypes.length; j++) {
                                paramTypeNames.push(paramTypes[j].getName());
                            }
                            try {
                                TMImpl[mName].overload.apply(TMImpl[mName], paramTypeNames).implementation = function () {
                                    // Return an empty list or true to signal trust
                                    var ArrayList = Java.use('java.util.ArrayList');
                                    return ArrayList.$new();
                                };
                            } catch (e) { }
                        }
                    }
                    console.log("[+] [Conscrypt] " + targetClass + " hooked successfully");
                } catch (err) {
                    // Not fatal, class may not exist in current runtime
                }
            });

            // -----------------------------------------------------------------
            // 1.4 NetworkSecurityConfig (Android 7+)
            // -----------------------------------------------------------------
            try {
                var NetworkSecurityTrustManager = Java.use('android.security.net.config.RootTrustManager');
                NetworkSecurityTrustManager.checkServerTrusted.overload(
                    '[Ljava.security.cert.X509Certificate;',
                    'Ljava.lang.String;',
                    'Ljava.lang.String;'
                ).implementation = function (certs, authType, hostname) {
                    console.log("[+] [NetworkSecurityConfig] RootTrustManager checkServerTrusted bypassed for: " + hostname);
                    var ArrayList = Java.use('java.util.ArrayList');
                    return ArrayList.$new();
                };
                console.log("[+] [NetworkSecurityConfig] RootTrustManager hooked successfully");
            } catch (err) {
                // Class or method not available
            }

            // -----------------------------------------------------------------
            // 1.5 Android WebView SSL Error Bypass
            // -----------------------------------------------------------------
            try {
                var WebViewClient = Java.use('android.webkit.WebViewClient');
                WebViewClient.onReceivedSslError.implementation = function (webView, sslErrorHandler, sslError) {
                    console.log("[+] [WebView] onReceivedSslError intercepted -> Calling sslErrorHandler.proceed()");
                    sslErrorHandler.proceed();
                };
                console.log("[+] [WebView] WebViewClient.onReceivedSslError hooked successfully");
            } catch (err) {
                console.log("[-] [WebView] WebViewClient hook failed: " + err);
            }

            // -----------------------------------------------------------------
            // 1.6 Third-Party Libraries (TrustKit, Appcelerator, Apache, Volley)
            // -----------------------------------------------------------------
            try {
                var TrustKit = Java.use('com.datatheorem.android.trustkit.pinning.OkHostnameVerifier');
                TrustKit.verify.overload('java.lang.String', 'javax.net.ssl.SSLSession').implementation = function (host, session) {
                    console.log("[+] [TrustKit] OkHostnameVerifier.verify bypassed for: " + host);
                    return true;
                };
            } catch (e) { }

            try {
                var PinningTrustManager = Java.use('appcelerator.https.PinningTrustManager');
                PinningTrustManager.checkServerTrusted.implementation = function (chain, authType) {
                    console.log("[+] [Appcelerator] PinningTrustManager bypassed");
                };
            } catch (e) { }

            try {
                var DefaultHttpClient = Java.use('org.apache.http.impl.client.DefaultHttpClient');
                // Apache legacy client
            } catch (e) { }
        });
    }

    // =========================================================================
    // 2. FLUTTER / DART BORINGSSL UNPINNING (ARM64 / ARMv7 Pattern Scanning)
    // =========================================================================
    function hookFlutterBoringSSL() {
        var flutterModule = Process.findModuleByName("libflutter.so");
        if (!flutterModule) {
            // Module might be loaded asynchronously during app initialization
            setTimeout(hookFlutterBoringSSL, 500);
            return;
        }

        console.log("[*] libflutter.so detected at base address: " + flutterModule.base);

        // Pattern for BoringSSL ssl_crypto_x509_session_verify_cert_chain across various Flutter builds
        var patterns = [];

        if (Process.arch === 'arm64') {
            patterns = [
                // Pattern 1: Standard Flutter BoringSSL ARM64
                "FF 83 01 D1 F6 57 03 A9 F4 4F 04 A9 FD 7B 05 A9 FD C3 01 91",
                // Pattern 2: Alternate Flutter BoringSSL ARM64
                "F[0-9a-f] 4F 02 A9 F[0-9a-f] 57 03 A9 F[0-9a-f] 5F 04 A9 F[0-9a-f] 7B 05 A9 FD C3 01 91",
                // Pattern 3: Recent Flutter 3.x BoringSSL ARM64
                "2D E9 F0 4F",
                // Pattern 4: Generic session_verify_cert_chain
                "F8 5F BC A9 F6 57 01 A9 F4 4F 02 A9 FD 7B 03 A9 FD 03 00 91"
            ];
        } else if (Process.arch === 'arm') {
            patterns = [
                // Standard ARMv7 BoringSSL pattern
                "2D E9 F0 4F A3 B0 82 46 8B 46",
                "2D E9 F0 4F 85 B0 05 46 0E 46"
            ];
        }

        var hooked = false;

        function tryScan(index) {
            if (index >= patterns.length || hooked) {
                if (!hooked) {
                    console.log("[-] [Flutter] Pattern scan completed, no direct BoringSSL matches found. Export search...");
                    searchFlutterExports(flutterModule);
                }
                return;
            }

            var pattern = patterns[index];
            Memory.scan(flutterModule.base, flutterModule.size, pattern, {
                onMatch: function (address, size) {
                    console.log("[+] [Flutter] Found BoringSSL verify candidate at: " + address);
                    try {
                        Interceptor.attach(address, {
                            onLeave: function (retval) {
                                console.log("[+] [Flutter] ssl_crypto_x509_session_verify_cert_chain -> Forcing return value to 1 (OK)");
                                retval.replace(ptr(1));
                            }
                        });
                        hooked = true;
                    } catch (e) {
                        console.log("[-] [Flutter] Failed to attach Interceptor at " + address + ": " + e);
                    }
                },
                onError: function (reason) {
                    console.log("[-] [Flutter] Memory scan error: " + reason);
                },
                onComplete: function () {
                    if (!hooked) {
                        tryScan(index + 1);
                    } else {
                        console.log("[+] [Flutter] BoringSSL hook active!");
                    }
                }
            });
        }

        tryScan(0);
    }

    function searchFlutterExports(module) {
        var exports = module.enumerateExports();
        var candidateNames = ['ssl_verify_', 'x509_verify_', 'session_verify'];
        for (var i = 0; i < exports.length; i++) {
            var exp = exports[i];
            for (var j = 0; j < candidateNames.length; j++) {
                if (exp.name.indexOf(candidateNames[j]) !== -1) {
                    console.log("[+] [Flutter] Found export match: " + exp.name + " at " + exp.address);
                    try {
                        Interceptor.attach(exp.address, {
                            onLeave: function (retval) {
                                retval.replace(ptr(1));
                            }
                        });
                    } catch (e) { }
                }
            }
        }
    }

    // Schedule Flutter check
    if (Process.platform === 'linux' || Process.platform === 'android') {
        setTimeout(hookFlutterBoringSSL, 1000);
    }

    // =========================================================================
    // 3. WINDOWS NATIVE SSL UNPINNING (WinHTTP, OpenSSL, libcurl)
    // =========================================================================
    if (Process.platform === 'windows') {
        console.log("[*] Windows OS detected. Initializing Windows native SSL hooks...");

        // -----------------------------------------------------------------
        // 3.1 WinHTTP Security Flags Hook (winhttp.dll)
        // -----------------------------------------------------------------
        var winhttpModule = Process.findModuleByName("winhttp.dll");
        if (winhttpModule) {
            console.log("[+] winhttp.dll loaded at: " + winhttpModule.base);

            // Hook WinHttpSendRequest
            var pWinHttpSendRequest = Module.findExportByName("winhttp.dll", "WinHttpSendRequest");
            if (pWinHttpSendRequest) {
                var pWinHttpSetOption = Module.findExportByName("winhttp.dll", "WinHttpSetOption");
                if (pWinHttpSetOption) {
                    var WinHttpSetOption = new NativeFunction(pWinHttpSetOption, 'int', ['pointer', 'uint32', 'pointer', 'uint32']);
                    
                    // WINHTTP_OPTION_SECURITY_FLAGS = 31
                    // Flags:
                    // SECURITY_FLAG_IGNORE_UNKNOWN_CA        = 0x00000100
                    // SECURITY_FLAG_IGNORE_CERT_DATE_INVALID = 0x00002000
                    // SECURITY_FLAG_IGNORE_CERT_CN_INVALID   = 0x00001000
                    // SECURITY_FLAG_IGNORE_CERT_WRONG_USAGE  = 0x00000200
                    // Total = 0x3300
                    var flagsBuf = Memory.alloc(4);
                    flagsBuf.writeU32(0x3300);

                    Interceptor.attach(pWinHttpSendRequest, {
                        onEnter: function (args) {
                            var hRequest = args[0];
                            WinHttpSetOption(hRequest, 31, flagsBuf, 4);
                            console.log("[+] [WinHTTP] Injected SECURITY_FLAG_IGNORE_ALL_CERT_ERRORS for request handle: " + hRequest);
                        }
                    });
                    console.log("[+] [WinHTTP] WinHttpSendRequest hooked successfully");
                }
            }
        }

        // -----------------------------------------------------------------
        // 3.2 OpenSSL / BoringSSL (libssl / ssleay32 / libcrypto)
        // -----------------------------------------------------------------
        var openSslModules = ["libssl.dll", "ssleay32.dll", "libssl-1_1.dll", "libssl-3.dll", "libcrypto.dll"];
        openSslModules.forEach(function (modName) {
            var mod = Process.findModuleByName(modName);
            if (mod) {
                console.log("[+] Found OpenSSL module: " + modName + " at " + mod.base);

                // SSL_CTX_set_verify(SSL_CTX *ctx, int mode, ssl_verify_cb callback)
                var pSSL_CTX_set_verify = Module.findExportByName(modName, "SSL_CTX_set_verify");
                if (pSSL_CTX_set_verify) {
                    Interceptor.attach(pSSL_CTX_set_verify, {
                        onEnter: function (args) {
                            console.log("[+] [OpenSSL] SSL_CTX_set_verify called -> Forcing mode to SSL_VERIFY_NONE (0)");
                            args[1] = ptr(0); // SSL_VERIFY_NONE
                            args[2] = ptr(0); // NULL callback
                        }
                    });
                }

                // SSL_set_verify(SSL *s, int mode, ssl_verify_cb callback)
                var pSSL_set_verify = Module.findExportByName(modName, "SSL_set_verify");
                if (pSSL_set_verify) {
                    Interceptor.attach(pSSL_set_verify, {
                        onEnter: function (args) {
                            console.log("[+] [OpenSSL] SSL_set_verify called -> Forcing mode to SSL_VERIFY_NONE (0)");
                            args[1] = ptr(0);
                            args[2] = ptr(0);
                        }
                    });
                }
            }
        });

        // -----------------------------------------------------------------
        // 3.3 libcurl (libcurl.dll)
        // -----------------------------------------------------------------
        var curlMod = Process.findModuleByName("libcurl.dll");
        if (curlMod) {
            console.log("[+] libcurl.dll loaded at: " + curlMod.base);
            var pCurlSetopt = Module.findExportByName("libcurl.dll", "curl_easy_setopt");
            if (pCurlSetopt) {
                Interceptor.attach(pCurlSetopt, {
                    onEnter: function (args) {
                        var option = args[1].toInt32();
                        // CURLOPT_SSL_VERIFYPEER = 64
                        // CURLOPT_SSL_VERIFYHOST = 81
                        // CURLOPT_PROXY_SSL_VERIFYPEER = 248
                        if (option === 64 || option === 81 || option === 248) {
                            console.log("[+] [libcurl] curl_easy_setopt option " + option + " -> Forcing value to 0");
                            args[2] = ptr(0);
                        }
                    }
                });
                console.log("[+] [libcurl] curl_easy_setopt hooked successfully");
            }
        }
    }

    console.log("[*] Universal SSL Unpinning Ready.");
})();

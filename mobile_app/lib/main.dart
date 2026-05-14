import 'package:flutter/material.dart';

import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'state/auth_state.dart';

void main() {
  runApp(const SportsStadiumApp());
}

class SportsStadiumApp extends StatefulWidget {
  const SportsStadiumApp({super.key});

  @override
  State<SportsStadiumApp> createState() => _SportsStadiumAppState();
}

class _SportsStadiumAppState extends State<SportsStadiumApp> {
  late final AuthState auth;

  @override
  void initState() {
    super.initState();
    auth = AuthState();
    auth.addListener(_onAuthChanged);
    auth.restoreSession();
  }

  @override
  void dispose() {
    auth.removeListener(_onAuthChanged);
    auth.dispose();
    super.dispose();
  }

  void _onAuthChanged() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '体育场馆预约系统',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2563EB)),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
        ),
        useMaterial3: true,
      ),
      home: auth.isLoading
          ? const _SplashScreen()
          : auth.isAuthenticated
          ? HomeScreen(auth: auth)
          : LoginScreen(auth: auth),
    );
  }
}

class _SplashScreen extends StatelessWidget {
  const _SplashScreen();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}

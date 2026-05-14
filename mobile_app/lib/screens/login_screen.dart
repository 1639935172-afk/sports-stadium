import 'package:flutter/material.dart';

import '../state/auth_state.dart';
import 'password_reset_screen.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.auth});

  final AuthState auth;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController(text: '18800000003');
  final _passwordController = TextEditingController(text: 'DemoPass123');
  bool _submitting = false;

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);
    final ok = await widget.auth.login(
      _phoneController.text,
      _passwordController.text,
    );
    if (!mounted) return;
    setState(() => _submitting = false);
    if (!ok) {
      _showMessage(widget.auth.errorMessage ?? '登录失败');
    }
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      '体育场馆预约系统',
                      style: Theme.of(context).textTheme.headlineMedium,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '普通用户移动端登录',
                      style: Theme.of(context).textTheme.bodyLarge,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    TextFormField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      decoration: const InputDecoration(
                        labelText: '手机号',
                        prefixIcon: Icon(Icons.phone_outlined),
                      ),
                      validator: (value) {
                        final text = value?.trim() ?? '';
                        if (text.length != 11 || int.tryParse(text) == null) {
                          return '请输入11位手机号';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _passwordController,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: '密码',
                        prefixIcon: Icon(Icons.lock_outline),
                      ),
                      validator: (value) =>
                          (value == null || value.isEmpty) ? '请输入密码' : null,
                    ),
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: _submitting ? null : _submit,
                      child: _submitting
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('登录'),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: _submitting
                          ? null
                          : () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) =>
                                      RegisterScreen(auth: widget.auth),
                                ),
                              );
                            },
                      child: const Text('注册新账号'),
                    ),
                    const SizedBox(height: 8),
                    TextButton(
                      onPressed: _submitting
                          ? null
                          : () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) =>
                                      PasswordResetScreen(auth: widget.auth),
                                ),
                              );
                            },
                      child: const Text('忘记密码'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

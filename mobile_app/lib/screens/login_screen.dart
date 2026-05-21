import 'package:flutter/material.dart';

import '../state/auth_state.dart';
import '../widgets/app_feedback.dart';
import '../widgets/auth_page_chrome.dart';
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
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  late bool _rememberPassword;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _phoneController.text = widget.auth.rememberedPhoneNumber;
    _passwordController.text = widget.auth.rememberedPassword;
    _rememberPassword = widget.auth.rememberPassword;
  }

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
      _phoneController.text.trim(),
      _passwordController.text,
      rememberPassword: _rememberPassword,
    );
    if (!mounted) return;
    setState(() => _submitting = false);
    if (!ok) {
      AppFeedback.showMessage(
        context,
        widget.auth.errorMessage ?? '登录失败',
        isError: true,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Align(
          alignment: Alignment.topCenter,
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 360),
              child: Form(
                key: _formKey,
                autovalidateMode: AutovalidateMode.onUserInteraction,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(width: 36, height: 36),
                        SizedBox(width: 12),
                        Expanded(child: SportLogo()),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const AuthTitle(),
                    const SizedBox(height: 12),
                    const Text(
                      '密码登录',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF111827),
                      ),
                    ),
                    const SizedBox(height: 8),
                    AuthTextField(
                      controller: _phoneController,
                      hintText: '手机号',
                      keyboardType: TextInputType.phone,
                      textInputAction: TextInputAction.next,
                      validator: (value) {
                        final text = value?.trim() ?? '';
                        if (text.length != 11 || int.tryParse(text) == null) {
                          return '请输入11位手机号';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 14),
                    AuthTextField(
                      controller: _passwordController,
                      hintText: '请输入密码',
                      obscureText: true,
                      textInputAction: TextInputAction.done,
                      onFieldSubmitted: (_) => _submitting ? null : _submit(),
                      validator: (value) =>
                          (value == null || value.isEmpty) ? '请输入密码' : null,
                    ),
                    const SizedBox(height: 8),
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      value: _rememberPassword,
                      onChanged: _submitting
                          ? null
                          : (value) {
                              setState(() {
                                _rememberPassword = value ?? false;
                              });
                            },
                      title: const Text(
                        '记住密码',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                      controlAffinity: ListTileControlAffinity.leading,
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      height: 50,
                      child: FilledButton(
                        style: FilledButton.styleFrom(
                          backgroundColor: colorScheme.primary,
                          foregroundColor: colorScheme.onPrimary,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(9),
                          ),
                          textStyle: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        onPressed: _submitting ? null : _submit,
                        child: _submitting
                            ? const AppLoadingIcon(size: 22)
                            : const Text('立即登录'),
                      ),
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

import 'package:flutter/material.dart';

import '../state/auth_state.dart';
import '../widgets/app_feedback.dart';
import '../widgets/auth_page_chrome.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key, required this.auth});

  final AuthState auth;

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _nicknameController = TextEditingController();
  final _password1Controller = TextEditingController();
  final _password2Controller = TextEditingController();
  final _codeController = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _phoneController.dispose();
    _nicknameController.dispose();
    _password1Controller.dispose();
    _password2Controller.dispose();
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);
    final ok = await widget.auth.register(
      phoneNumber: _phoneController.text.trim(),
      nickname: _nicknameController.text.trim(),
      password1: _password1Controller.text,
      password2: _password2Controller.text,
      verificationCode: _codeController.text.trim(),
    );
    if (!mounted) return;
    setState(() => _submitting = false);
    if (ok) {
      AppFeedback.showMessage(context, '注册成功，请登录');
      Navigator.of(context).pop();
    } else {
      AppFeedback.showMessage(
        context,
        widget.auth.errorMessage ?? '注册失败',
        isError: true,
      );
    }
  }

  void _fillDevCode() {
    _codeController.text = '123456';
    AppFeedback.showMessage(context, '验证码已填入');
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
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        AuthBackButton(
                          onPressed: () => Navigator.of(context).pop(),
                        ),
                        const SizedBox(width: 12),
                        const Expanded(child: SportLogo()),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const AuthTitle(),
                    const SizedBox(height: 12),
                    const Text(
                      '注册',
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
                      controller: _password1Controller,
                      hintText: '请设置密码',
                      obscureText: true,
                      textInputAction: TextInputAction.next,
                      validator: (value) =>
                          (value == null || value.length < 8) ? '密码至少8位' : null,
                    ),
                    const SizedBox(height: 14),
                    AuthTextField(
                      controller: _password2Controller,
                      hintText: '再次输入密码',
                      obscureText: true,
                      textInputAction: TextInputAction.next,
                      validator: (value) => value != _password1Controller.text
                          ? '两次输入的密码不一致'
                          : null,
                    ),
                    const SizedBox(height: 14),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: AuthTextField(
                            controller: _codeController,
                            hintText: '输入验证码',
                            keyboardType: TextInputType.number,
                            textInputAction: TextInputAction.done,
                            onFieldSubmitted: (_) =>
                                _submitting ? null : _submit(),
                            validator: (value) =>
                                (value == null || value.isEmpty)
                                ? '请输入验证码'
                                : null,
                          ),
                        ),
                        const SizedBox(width: 12),
                        SizedBox(
                          height: 48,
                          child: FilledButton(
                            style: FilledButton.styleFrom(
                              backgroundColor: const Color(0xFF3FA9F5),
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 14,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                              textStyle: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            onPressed: _submitting ? null : _fillDevCode,
                            child: const Text('获取验证码'),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 18),
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
                            : const Text('立即注册'),
                      ),
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

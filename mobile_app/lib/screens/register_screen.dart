import 'package:flutter/material.dart';

import '../state/auth_state.dart';
import '../widgets/app_feedback.dart';

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
  final _codeController = TextEditingController(text: '123456');
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
      phoneNumber: _phoneController.text,
      nickname: _nicknameController.text,
      password1: _password1Controller.text,
      password2: _password2Controller.text,
      verificationCode: _codeController.text,
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('注册账号')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _formKey,
                autovalidateMode: AutovalidateMode.onUserInteraction,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: '手机号',
                    prefixIcon: Icon(Icons.phone_outlined),
                  ),
                  textInputAction: TextInputAction.next,
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
                  controller: _nicknameController,
                  decoration: const InputDecoration(
                    labelText: '昵称',
                    prefixIcon: Icon(Icons.person_outline),
                  ),
                  textInputAction: TextInputAction.next,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _password1Controller,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: '密码',
                    prefixIcon: Icon(Icons.lock_outline),
                  ),
                  textInputAction: TextInputAction.next,
                  validator: (value) =>
                      (value == null || value.length < 8) ? '密码至少8位' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _password2Controller,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: '确认密码',
                    prefixIcon: Icon(Icons.lock_reset),
                  ),
                  textInputAction: TextInputAction.next,
                  validator: (value) =>
                      value != _password1Controller.text ? '两次输入的密码不一致' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _codeController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: '验证码',
                    helperText: '开发环境验证码：123456',
                    prefixIcon: Icon(Icons.verified_outlined),
                  ),
                  textInputAction: TextInputAction.done,
                  onFieldSubmitted: (_) => _submitting ? null : _submit(),
                  validator: (value) =>
                      (value == null || value.isEmpty) ? '请输入验证码' : null,
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _submitting ? null : _submit,
                  child: _submitting
                      ? const AppLoadingIcon(size: 20)
                      : const Text('注册'),
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

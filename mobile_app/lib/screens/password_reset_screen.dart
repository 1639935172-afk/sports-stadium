import 'package:flutter/material.dart';

import '../state/auth_state.dart';

class PasswordResetScreen extends StatefulWidget {
  const PasswordResetScreen({super.key, required this.auth});

  final AuthState auth;

  @override
  State<PasswordResetScreen> createState() => _PasswordResetScreenState();
}

class _PasswordResetScreenState extends State<PasswordResetScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _verificationCodeController = TextEditingController(text: '123456');
  final _newPassword1Controller = TextEditingController();
  final _newPassword2Controller = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _phoneController.dispose();
    _verificationCodeController.dispose();
    _newPassword1Controller.dispose();
    _newPassword2Controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);
    final ok = await widget.auth.resetPassword(
      phoneNumber: _phoneController.text,
      verificationCode: _verificationCodeController.text,
      newPassword1: _newPassword1Controller.text,
      newPassword2: _newPassword2Controller.text,
    );
    if (!mounted) return;
    setState(() => _submitting = false);
    if (ok) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('密码已重置，请使用新密码登录。')));
      Navigator.of(context).pop();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(widget.auth.errorMessage ?? '重置密码失败。')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('找回密码')),
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
                      controller: _verificationCodeController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: '验证码',
                        prefixIcon: Icon(Icons.verified_outlined),
                      ),
                      validator: (value) =>
                          (value == null || value.trim().isEmpty)
                          ? '请输入验证码'
                          : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _newPassword1Controller,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: '新密码',
                        prefixIcon: Icon(Icons.lock_outline),
                      ),
                      validator: (value) =>
                          (value == null || value.isEmpty) ? '请输入新密码' : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _newPassword2Controller,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: '确认新密码',
                        prefixIcon: Icon(Icons.lock_reset_outlined),
                      ),
                      validator: (value) =>
                          (value == null || value.isEmpty) ? '请再次输入新密码' : null,
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
                          : const Text('重置密码'),
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

import 'package:flutter/material.dart';

import '../models/app_user.dart';
import '../state/auth_state.dart';
import '../widgets/app_feedback.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key, required this.auth});

  final AuthState auth;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  var isLoading = false;
  String? errorMessage;

  Future<void> _refreshProfile() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final user = await widget.auth.api.profile();
      if (!mounted) return;
      setState(() {
        widget.auth.user = user;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载个人资料，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _editProfile() async {
    final user = widget.auth.user;
    if (user == null) return;
    final nicknameController = TextEditingController(text: user.nickname);

    final nickname = await showDialog<String>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('修改资料'),
          content: TextField(
            controller: nicknameController,
            decoration: const InputDecoration(labelText: '昵称'),
            maxLength: 50,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () =>
                  Navigator.of(context).pop(nicknameController.text),
              child: const Text('保存'),
            ),
          ],
        );
      },
    );
    nicknameController.dispose();

    if (nickname == null) return;
    final success = await widget.auth.updateProfile(nickname: nickname);
    if (!mounted) return;
    AppFeedback.showMessage(
      context,
      success ? '个人资料已更新。' : widget.auth.errorMessage ?? '修改资料失败。',
      isError: !success,
    );
    if (success) setState(() {});
  }

  Future<void> _changePassword() async {
    final oldPasswordController = TextEditingController();
    final newPassword1Controller = TextEditingController();
    final newPassword2Controller = TextEditingController();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('修改密码'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: oldPasswordController,
                obscureText: true,
                decoration: const InputDecoration(labelText: '当前密码'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: newPassword1Controller,
                obscureText: true,
                decoration: const InputDecoration(labelText: '新密码'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: newPassword2Controller,
                obscureText: true,
                decoration: const InputDecoration(labelText: '确认新密码'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('保存'),
            ),
          ],
        );
      },
    );

    if (confirmed != true) {
      oldPasswordController.dispose();
      newPassword1Controller.dispose();
      newPassword2Controller.dispose();
      return;
    }

    final success = await widget.auth.changePassword(
      oldPassword: oldPasswordController.text,
      newPassword1: newPassword1Controller.text,
      newPassword2: newPassword2Controller.text,
    );
    oldPasswordController.dispose();
    newPassword1Controller.dispose();
    newPassword2Controller.dispose();

    if (!mounted) return;
    AppFeedback.showMessage(
      context,
      success ? '密码已修改。' : widget.auth.errorMessage ?? '修改密码失败。',
      isError: !success,
    );
  }

  Future<void> _cancelAccount() async {
    final passwordController = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('注销账号'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('注销后账号将不能继续登录。请输入当前密码确认。'),
              const SizedBox(height: 12),
              TextField(
                controller: passwordController,
                obscureText: true,
                decoration: const InputDecoration(labelText: '当前密码'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('确认注销'),
            ),
          ],
        );
      },
    );

    if (confirmed != true) {
      passwordController.dispose();
      return;
    }

    final success = await widget.auth.cancelAccount(
      password: passwordController.text,
    );
    passwordController.dispose();

    if (!mounted) return;
    AppFeedback.showMessage(
      context,
      success ? '账号已注销。' : widget.auth.errorMessage ?? '注销账号失败。',
      isError: !success,
    );
    if (success) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.auth.user;
    return Scaffold(
      appBar: AppBar(centerTitle: true, title: const Text('个人资料')),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _refreshProfile,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            children: [
              if (errorMessage != null) ...[
                _ErrorPanel(message: errorMessage!, onRetry: _refreshProfile),
                const SizedBox(height: 12),
              ],
              if (user == null)
                const AppMessagePanel(
                  icon: Icons.account_circle_outlined,
                  message: '暂无个人资料。',
                  topPadding: 0,
                )
              else
                _ProfileCard(
                  user: user,
                  onEditProfile: _editProfile,
                  onChangePassword: _changePassword,
                  onCancelAccount: _cancelAccount,
                ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: isLoading ? null : _refreshProfile,
                icon: isLoading
                    ? const AppLoadingIcon()
                    : const Icon(Icons.refresh),
                label: const Text('刷新资料'),
              ),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: widget.auth.logout,
                icon: const Icon(Icons.logout),
                label: const Text('退出登录'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProfileCard extends StatelessWidget {
  const _ProfileCard({
    required this.user,
    required this.onEditProfile,
    required this.onChangePassword,
    required this.onCancelAccount,
  });

  final AppUser user;
  final VoidCallback onEditProfile;
  final VoidCallback onChangePassword;
  final VoidCallback onCancelAccount;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _ProfileRow(label: '手机号', value: user.phoneNumber),
            _ProfileRow(
              label: '昵称',
              value: user.nickname.isEmpty ? '未设置' : user.nickname,
            ),
            _ProfileRow(label: '角色', value: _roleLabel(user.role)),
            _ProfileRow(label: '账号状态', value: _statusLabel(user)),
            const SizedBox(height: 12),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                ActionChip(
                  avatar: const Icon(Icons.edit_outlined, size: 18),
                  label: const Text('修改资料'),
                  onPressed: onEditProfile,
                ),
                ActionChip(
                  avatar: const Icon(Icons.lock_outline, size: 18),
                  label: const Text('修改密码'),
                  onPressed: onChangePassword,
                ),
                ActionChip(
                  avatar: const Icon(Icons.person_off, size: 18),
                  label: const Text('注销账号'),
                  onPressed: onCancelAccount,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _roleLabel(String role) {
    return switch (role) {
      'ordinary' => '普通用户',
      'stadium_admin' => '场馆管理员',
      'system_admin' => '系统管理员',
      _ => role,
    };
  }

  String _statusLabel(AppUser user) {
    if (user.isCancelled) return '已注销';
    if (!user.isActive) return '已禁用';
    return '正常';
  }
}

class _ProfileRow extends StatelessWidget {
  const _ProfileRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 86,
            child: Text(
              '$label：',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

class _ErrorPanel extends StatelessWidget {
  const _ErrorPanel({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: AppMessagePanel(
          icon: Icons.cloud_off,
          message: message,
          action: TextButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('重试'),
          ),
          topPadding: 0,
        ),
      ),
    );
  }
}

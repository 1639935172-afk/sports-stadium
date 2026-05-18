import 'package:flutter/material.dart';

import '../api/system_user_api.dart';
import '../models/app_user.dart';

class SystemUserListScreen extends StatefulWidget {
  const SystemUserListScreen({
    super.key,
    required this.api,
    required this.currentUserId,
  });

  final SystemUserApi api;
  final int currentUserId;

  @override
  State<SystemUserListScreen> createState() => _SystemUserListScreenState();
}

class _SystemUserListScreenState extends State<SystemUserListScreen> {
  final searchController = TextEditingController();
  var users = <AppUser>[];
  var isLoading = true;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  Future<void> _loadUsers() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final result = await widget.api.list(query: searchController.text);
      if (!mounted) return;
      setState(() {
        users = result;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载用户列表，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _editUser(AppUser user) async {
    final nicknameController = TextEditingController(text: user.nickname);
    var role = user.role;
    var isActive = user.isActive;
    var isCancelled = user.isCancelled;

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: Text('编辑用户 ${user.phoneNumber}'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      controller: nicknameController,
                      decoration: const InputDecoration(labelText: '昵称'),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: role,
                      decoration: const InputDecoration(labelText: '角色'),
                      items: const [
                        DropdownMenuItem(
                          value: 'ordinary',
                          child: Text('普通用户'),
                        ),
                        DropdownMenuItem(
                          value: 'stadium_admin',
                          child: Text('场馆管理员'),
                        ),
                        DropdownMenuItem(
                          value: 'system_admin',
                          child: Text('系统管理员'),
                        ),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setDialogState(() {
                          role = value;
                        });
                      },
                    ),
                    const SizedBox(height: 12),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('允许登录'),
                      value: isActive,
                      onChanged: isCancelled
                          ? null
                          : (value) {
                              setDialogState(() {
                                isActive = value;
                              });
                            },
                    ),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('已注销'),
                      value: isCancelled,
                      onChanged: (value) {
                        setDialogState(() {
                          isCancelled = value;
                          if (value) {
                            isActive = false;
                          }
                        });
                      },
                    ),
                  ],
                ),
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
      },
    );

    if (saved != true) {
      nicknameController.dispose();
      return;
    }

    try {
      await widget.api.update(
        id: user.id,
        nickname: nicknameController.text.trim(),
        role: role,
        isActive: isActive,
        isCancelled: isCancelled,
      );
      nicknameController.dispose();
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('用户信息已更新。')));
      await _loadUsers();
    } catch (_) {
      nicknameController.dispose();
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('更新用户失败，请稍后重试。')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('用户管理')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: searchController,
                    textInputAction: TextInputAction.search,
                    decoration: const InputDecoration(
                      labelText: '搜索用户',
                      hintText: '输入手机号或昵称',
                      prefixIcon: Icon(Icons.search),
                    ),
                    onSubmitted: (_) => _loadUsers(),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton.icon(
                  onPressed: isLoading ? null : _loadUsers,
                  icon: const Icon(Icons.search),
                  label: const Text('搜索'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (isLoading)
              const Padding(
                padding: EdgeInsets.only(top: 80),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (errorMessage != null)
              _MessagePanel(
                icon: Icons.cloud_off,
                message: errorMessage!,
                action: TextButton.icon(
                  onPressed: _loadUsers,
                  icon: const Icon(Icons.refresh),
                  label: const Text('重试'),
                ),
              )
            else if (users.isEmpty)
              const _MessagePanel(
                icon: Icons.people_alt_outlined,
                message: '暂无符合条件的用户。',
              )
            else
              for (final user in users) ...[
                _UserCard(
                  user: user,
                  isCurrentUser: user.id == widget.currentUserId,
                  onEdit: user.id == widget.currentUserId
                      ? null
                      : () => _editUser(user),
                ),
                const SizedBox(height: 12),
              ],
          ],
        ),
      ),
    );
  }
}

class _UserCard extends StatelessWidget {
  const _UserCard({
    required this.user,
    required this.isCurrentUser,
    required this.onEdit,
  });

  final AppUser user;
  final bool isCurrentUser;
  final VoidCallback? onEdit;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    user.phoneNumber,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                if (isCurrentUser)
                  const Chip(label: Text('当前账号'))
                else
                  OutlinedButton.icon(
                    onPressed: onEdit,
                    icon: const Icon(Icons.edit_outlined),
                    label: const Text('编辑'),
                  ),
              ],
            ),
            const SizedBox(height: 10),
            _InfoRow(
              label: '昵称',
              value: user.nickname.isEmpty ? '未设置' : user.nickname,
            ),
            _InfoRow(label: '角色', value: _roleLabel(user.role)),
            _InfoRow(label: '登录状态', value: user.isActive ? '允许登录' : '禁止登录'),
            _InfoRow(label: '账号状态', value: user.isCancelled ? '已注销' : '正常'),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 72, child: Text(label)),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

class _MessagePanel extends StatelessWidget {
  const _MessagePanel({required this.icon, required this.message, this.action});

  final IconData icon;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 72),
      child: Center(
        child: Column(
          children: [
            Icon(icon, size: 48, color: Theme.of(context).colorScheme.outline),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            if (action != null) ...[const SizedBox(height: 8), action!],
          ],
        ),
      ),
    );
  }
}

String _roleLabel(String role) {
  return switch (role) {
    'ordinary' => '普通用户',
    'stadium_admin' => '场馆管理员',
    'system_admin' => '系统管理员',
    _ => role,
  };
}

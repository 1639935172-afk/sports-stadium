import 'package:flutter/material.dart';

import '../api/stadium_api.dart';
import '../models/stadium.dart';

class AdminStadiumAuditScreen extends StatefulWidget {
  const AdminStadiumAuditScreen({super.key, required this.api});

  final StadiumApi api;

  @override
  State<AdminStadiumAuditScreen> createState() =>
      _AdminStadiumAuditScreenState();
}

class _AdminStadiumAuditScreenState extends State<AdminStadiumAuditScreen> {
  var stadiums = <Stadium>[];
  var isLoading = true;
  var handlingStadiumId = 0;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadStadiums();
  }

  Future<void> _loadStadiums() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final result = await widget.api.adminPending();
      if (!mounted) return;
      setState(() {
        stadiums = result;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载待审核场馆，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _handleStadium(Stadium stadium, bool approve) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(approve ? '通过场馆' : '驳回场馆'),
          content: Text('确认${approve ? '通过' : '驳回'} ${stadium.name} 吗？'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: Text(approve ? '确认通过' : '确认驳回'),
            ),
          ],
        );
      },
    );

    if (confirmed != true) return;

    setState(() {
      handlingStadiumId = stadium.id;
    });

    try {
      var successMessage = '场馆已${approve ? '通过' : '驳回'}。';
      if (approve) {
        final result = await widget.api.approve(stadiumId: stadium.id);
        if (result.action == 'deleted') {
          successMessage = result.detail.isEmpty ? '场馆删除申请已通过。' : result.detail;
        }
      } else {
        await widget.api.reject(stadiumId: stadium.id);
      }
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(successMessage)));
      await _loadStadiums();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${approve ? '通过' : '驳回'}场馆失败，请稍后重试。')),
      );
    } finally {
      if (mounted) {
        setState(() {
          handlingStadiumId = 0;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(centerTitle: true, title: const Text('场馆审核')),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadStadiums,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            children: [
              if (isLoading)
                const Padding(
                  padding: EdgeInsets.only(top: 120),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (errorMessage != null)
                _MessagePanel(
                  icon: Icons.cloud_off,
                  message: errorMessage!,
                  action: TextButton.icon(
                    onPressed: _loadStadiums,
                    icon: const Icon(Icons.refresh),
                    label: const Text('重试'),
                  ),
                )
              else if (stadiums.isEmpty)
                const _MessagePanel(
                  icon: Icons.approval_outlined,
                  message: '当前没有待审核场馆。',
                )
              else
                for (final stadium in stadiums) ...[
                  _StadiumCard(
                    stadium: stadium,
                    isHandling: handlingStadiumId == stadium.id,
                    onApprove: handlingStadiumId == 0
                        ? () => _handleStadium(stadium, true)
                        : null,
                    onReject: handlingStadiumId == 0
                        ? () => _handleStadium(stadium, false)
                        : null,
                  ),
                  const SizedBox(height: 12),
                ],
            ],
          ),
        ),
      ),
    );
  }
}

class _StadiumCard extends StatelessWidget {
  const _StadiumCard({
    required this.stadium,
    required this.isHandling,
    required this.onApprove,
    required this.onReject,
  });

  final Stadium stadium;
  final bool isHandling;
  final VoidCallback? onApprove;
  final VoidCallback? onReject;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(stadium.name, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 10),
            _InfoRow(label: '负责人', value: _ownerLabel(stadium)),
            _InfoRow(label: '状态', value: _statusLabel(stadium.auditStatus)),
            if (stadium.deletionRequested)
              const _InfoRow(label: '类型', value: '删除申请'),
            _InfoRow(label: '地址', value: stadium.address),
            _InfoRow(label: '电话', value: stadium.phoneNumber),
            if (stadium.information.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(stadium.information),
            ],
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: onApprove,
                  icon: isHandling
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.check_circle_outline),
                  label: const Text('通过'),
                ),
                OutlinedButton.icon(
                  onPressed: onReject,
                  icon: const Icon(Icons.cancel_outlined),
                  label: const Text('驳回'),
                ),
              ],
            ),
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
          SizedBox(width: 56, child: Text(label)),
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

String _statusLabel(String status) {
  return switch (status) {
    'pending' => '待审核',
    'approved' => '已通过',
    'rejected' => '已驳回',
    _ => status,
  };
}

String _ownerLabel(Stadium stadium) {
  final nickname = stadium.ownerNickname.isEmpty
      ? '未设置昵称'
      : stadium.ownerNickname;
  final phone = stadium.ownerPhoneNumber.isEmpty
      ? stadium.phoneNumber
      : stadium.ownerPhoneNumber;
  return '$nickname ($phone)';
}

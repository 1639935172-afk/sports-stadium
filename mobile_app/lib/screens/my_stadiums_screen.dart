import 'package:flutter/material.dart';
import 'package:dio/dio.dart';

import '../api/stadium_api.dart';
import '../models/stadium.dart';
import 'field_management_screen.dart';
import 'stadium_form_screen.dart';

class MyStadiumsScreen extends StatefulWidget {
  const MyStadiumsScreen({super.key, required this.api});

  final StadiumApi api;

  @override
  State<MyStadiumsScreen> createState() => _MyStadiumsScreenState();
}

class _MyStadiumsScreenState extends State<MyStadiumsScreen> {
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
      final result = await widget.api.mine();
      if (!mounted) return;
      setState(() {
        stadiums = result;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载我的场馆，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _createStadium() async {
    final formValue = await Navigator.of(context).push<StadiumFormValue>(
      MaterialPageRoute<StadiumFormValue>(
        builder: (_) => const StadiumFormScreen(),
      ),
    );
    if (formValue == null) return;

    try {
      await widget.api.createManaged(
        name: formValue.name,
        address: formValue.address,
        phoneNumber: formValue.phoneNumber,
        information: formValue.information,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('场馆已提交审核。')));
      await _loadStadiums();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_readError(error, fallback: '提交场馆失败，请稍后重试。'))),
      );
    }
  }

  Future<void> _editStadium(Stadium stadium) async {
    final formValue = await Navigator.of(context).push<StadiumFormValue>(
      MaterialPageRoute<StadiumFormValue>(
        builder: (_) => StadiumFormScreen(initialStadium: stadium),
      ),
    );
    if (formValue == null) return;

    setState(() {
      handlingStadiumId = stadium.id;
    });
    try {
      await widget.api.updateManaged(
        stadiumId: stadium.id,
        name: formValue.name,
        address: formValue.address,
        phoneNumber: formValue.phoneNumber,
        information: formValue.information,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('场馆修改已重新提交审核。')));
      await _loadStadiums();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_readError(error, fallback: '修改场馆失败，请稍后重试。'))),
      );
    } finally {
      if (mounted) {
        setState(() {
          handlingStadiumId = 0;
        });
      }
    }
  }

  Future<void> _requestDeletion(Stadium stadium) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('申请删除场馆'),
          content: Text('确认提交 ${stadium.name} 的删除申请吗？'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('确认申请'),
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
      await widget.api.requestDeletion(stadiumId: stadium.id);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('删除申请已提交审核。')));
      await _loadStadiums();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_readError(error, fallback: '提交删除申请失败，请稍后重试。'))),
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
      appBar: AppBar(title: const Text('我的场馆')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _createStadium,
        icon: const Icon(Icons.add_business_outlined),
        label: const Text('新增场馆'),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadStadiums,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
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
                  icon: Icons.storefront_outlined,
                  message: '还没有提交过场馆。',
                )
              else
                for (final stadium in stadiums) ...[
                  _MyStadiumCard(
                    stadium: stadium,
                    isHandling: handlingStadiumId == stadium.id,
                    onManageFields:
                        handlingStadiumId == 0 &&
                            stadium.auditStatus == 'approved' &&
                            stadium.isOpen &&
                            !stadium.deletionRequested
                        ? () => _openFieldManagement(stadium)
                        : null,
                    onEdit: handlingStadiumId == 0
                        ? () => _editStadium(stadium)
                        : null,
                    onDeleteRequest:
                        handlingStadiumId == 0 && !stadium.deletionRequested
                        ? () => _requestDeletion(stadium)
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

  void _openFieldManagement(Stadium stadium) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) =>
            FieldManagementScreen(api: widget.api, stadium: stadium),
      ),
    );
  }
}

String _readError(Object error, {required String fallback}) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map) {
      final message = data.entries
          .map((entry) => '${entry.key}: ${_stringify(entry.value)}')
          .join('\n');
      if (message.isNotEmpty) return message;
    }
    if (data is List) {
      final message = data.map(_stringify).join('\n');
      if (message.isNotEmpty) return message;
    }
    if (data is String && data.isNotEmpty) {
      return data;
    }
  }
  return fallback;
}

String _stringify(Object? value) {
  if (value is List) {
    return value.join('，');
  }
  return value?.toString() ?? '';
}

class _MyStadiumCard extends StatelessWidget {
  const _MyStadiumCard({
    required this.stadium,
    required this.isHandling,
    required this.onManageFields,
    required this.onEdit,
    required this.onDeleteRequest,
  });

  final Stadium stadium;
  final bool isHandling;
  final VoidCallback? onManageFields;
  final VoidCallback? onEdit;
  final VoidCallback? onDeleteRequest;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    stadium.name,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                if (stadium.deletionRequested)
                  const Chip(label: Text('删除申请中'))
                else
                  Chip(label: Text(_statusLabel(stadium.auditStatus))),
              ],
            ),
            const SizedBox(height: 10),
            _InfoRow(label: '地址', value: stadium.address),
            _InfoRow(label: '电话', value: stadium.phoneNumber),
            _InfoRow(label: '开放状态', value: stadium.isOpen ? '开放' : '未开放'),
            if (stadium.information.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(stadium.information),
            ],
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (onManageFields != null)
                  OutlinedButton.icon(
                    onPressed: onManageFields,
                    icon: const Icon(Icons.grid_view_outlined),
                    label: const Text('场地管理'),
                  ),
                FilledButton.icon(
                  onPressed: onEdit,
                  icon: isHandling
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.edit_outlined),
                  label: const Text('编辑'),
                ),
                OutlinedButton.icon(
                  onPressed: onDeleteRequest,
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('申请删除'),
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
          SizedBox(width: 64, child: Text(label)),
          Expanded(child: Text(value.isEmpty ? '未填写' : value)),
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

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../api/stadium_api.dart';
import '../models/stadium.dart';
import 'field_form_screen.dart';
import 'time_slot_management_screen.dart';

class FieldManagementScreen extends StatefulWidget {
  const FieldManagementScreen({
    super.key,
    required this.api,
    required this.stadium,
  });

  final StadiumApi api;
  final Stadium stadium;

  @override
  State<FieldManagementScreen> createState() => _FieldManagementScreenState();
}

class _FieldManagementScreenState extends State<FieldManagementScreen> {
  var fields = <StadiumField>[];
  var isLoading = true;
  var handlingFieldId = 0;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadFields();
  }

  Future<void> _loadFields() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final result = await widget.api.fields(stadiumId: widget.stadium.id);
      if (!mounted) return;
      setState(() {
        fields = result;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载场地列表，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _createField() async {
    final formValue = await Navigator.of(context).push<FieldFormValue>(
      MaterialPageRoute<FieldFormValue>(
        builder: (_) => const FieldFormScreen(),
      ),
    );
    if (formValue == null) return;

    try {
      await widget.api.createField(
        stadiumId: widget.stadium.id,
        fieldType: formValue.fieldType,
        number: formValue.number,
        isActive: formValue.isActive,
        pricePerHour: formValue.pricePerHour,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('场地已创建。')));
      await _loadFields();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_readError(error, '创建场地失败。'))));
    }
  }

  Future<void> _editField(StadiumField field) async {
    final formValue = await Navigator.of(context).push<FieldFormValue>(
      MaterialPageRoute<FieldFormValue>(
        builder: (_) => FieldFormScreen(initialField: field),
      ),
    );
    if (formValue == null) return;

    setState(() {
      handlingFieldId = field.id;
    });
    try {
      await widget.api.updateField(
        fieldId: field.id,
        fieldType: formValue.fieldType,
        number: formValue.number,
        isActive: formValue.isActive,
        pricePerHour: formValue.pricePerHour,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('场地已更新。')));
      await _loadFields();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_readError(error, '更新场地失败。'))));
    } finally {
      if (mounted) {
        setState(() {
          handlingFieldId = 0;
        });
      }
    }
  }

  Future<void> _disableField(StadiumField field) async {
    setState(() {
      handlingFieldId = field.id;
    });
    try {
      await widget.api.disableField(fieldId: field.id);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('场地已停用。')));
      await _loadFields();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_readError(error, '停用场地失败。'))));
    } finally {
      if (mounted) {
        setState(() {
          handlingFieldId = 0;
        });
      }
    }
  }

  Future<void> _deleteField(StadiumField field) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('删除场地'),
          content: Text('确认删除 ${field.fieldType} ${field.number} 吗？'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('确认删除'),
            ),
          ],
        );
      },
    );
    if (confirmed != true) return;

    setState(() {
      handlingFieldId = field.id;
    });
    try {
      await widget.api.deleteField(fieldId: field.id);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('场地已删除。')));
      await _loadFields();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_readError(error, '删除场地失败。'))));
    } finally {
      if (mounted) {
        setState(() {
          handlingFieldId = 0;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        centerTitle: true,
        title: Text('${widget.stadium.name} - 场地管理'),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _createField,
        icon: const Icon(Icons.add),
        label: const Text('新增场地'),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadFields,
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
                    onPressed: _loadFields,
                    icon: const Icon(Icons.refresh),
                    label: const Text('重试'),
                  ),
                )
              else if (fields.isEmpty)
                const _MessagePanel(
                  icon: Icons.sports_tennis_outlined,
                  message: '当前还没有场地。',
                )
              else
                for (final field in fields) ...[
                  _FieldCard(
                    field: field,
                    isHandling: handlingFieldId == field.id,
                    onManageTimeSlots: handlingFieldId == 0
                        ? () => _openTimeSlotManagement(field)
                        : null,
                    onEdit: handlingFieldId == 0
                        ? () => _editField(field)
                        : null,
                    onDisable: handlingFieldId == 0 && field.isActive
                        ? () => _disableField(field)
                        : null,
                    onDelete: handlingFieldId == 0
                        ? () => _deleteField(field)
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

  void _openTimeSlotManagement(StadiumField field) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => TimeSlotManagementScreen(api: widget.api, field: field),
      ),
    );
  }
}

class _FieldCard extends StatelessWidget {
  const _FieldCard({
    required this.field,
    required this.isHandling,
    required this.onManageTimeSlots,
    required this.onEdit,
    required this.onDisable,
    required this.onDelete,
  });

  final StadiumField field;
  final bool isHandling;
  final VoidCallback? onManageTimeSlots;
  final VoidCallback? onEdit;
  final VoidCallback? onDisable;
  final VoidCallback? onDelete;

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
                    '${field.fieldType} ${field.number}'.trim(),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Chip(label: Text(field.isActive ? '已启用' : '已停用')),
              ],
            ),
            const SizedBox(height: 10),
            _InfoRow(label: '编号', value: field.number),
            _InfoRow(label: '类型', value: field.fieldType),
            _InfoRow(label: '价格', value: '${field.pricePerHour} 元/小时'),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: onManageTimeSlots,
                  icon: const Icon(Icons.schedule_outlined),
                  label: const Text('时段管理'),
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
                  onPressed: onDisable,
                  icon: const Icon(Icons.pause_circle_outline),
                  label: const Text('停用'),
                ),
                OutlinedButton.icon(
                  onPressed: onDelete,
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('删除'),
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

String _readError(Object error, String fallback) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map) {
      final message = data.entries
          .map((entry) => '${entry.key}: ${_stringify(entry.value)}')
          .join('\n');
      if (message.isNotEmpty) return message;
    }
    if (data is String && data.isNotEmpty) return data;
  }
  return fallback;
}

String _stringify(Object? value) {
  if (value is List) return value.join('，');
  return value?.toString() ?? '';
}

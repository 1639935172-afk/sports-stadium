import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../api/stadium_api.dart';
import '../models/stadium.dart';
import 'time_slot_form_screen.dart';

class TimeSlotManagementScreen extends StatefulWidget {
  const TimeSlotManagementScreen({
    super.key,
    required this.api,
    required this.field,
  });

  final StadiumApi api;
  final StadiumField field;

  @override
  State<TimeSlotManagementScreen> createState() =>
      _TimeSlotManagementScreenState();
}

class _TimeSlotManagementScreenState extends State<TimeSlotManagementScreen> {
  var timeSlots = <TimeSlot>[];
  var isLoading = true;
  var handlingTimeSlotId = 0;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadTimeSlots();
  }

  Future<void> _loadTimeSlots() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final result = await widget.api.timeSlots(fieldId: widget.field.id);
      if (!mounted) return;
      setState(() {
        timeSlots = result;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载时段列表，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _createTimeSlot() async {
    final formValue = await Navigator.of(context).push<TimeSlotFormValue>(
      MaterialPageRoute<TimeSlotFormValue>(
        builder: (_) => const TimeSlotFormScreen(),
      ),
    );
    if (formValue == null) return;

    try {
      await widget.api.createTimeSlot(
        fieldId: widget.field.id,
        date: formValue.date,
        startTime: formValue.startTime,
        endTime: formValue.endTime,
        isAvailable: formValue.isAvailable,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('时段已创建。')));
      await _loadTimeSlots();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_readError(error, '创建时段失败。'))));
    }
  }

  Future<void> _editTimeSlot(TimeSlot slot) async {
    final formValue = await Navigator.of(context).push<TimeSlotFormValue>(
      MaterialPageRoute<TimeSlotFormValue>(
        builder: (_) => TimeSlotFormScreen(initialSlot: slot),
      ),
    );
    if (formValue == null) return;

    setState(() {
      handlingTimeSlotId = slot.id;
    });
    try {
      await widget.api.updateTimeSlot(
        timeSlotId: slot.id,
        date: formValue.date,
        startTime: formValue.startTime,
        endTime: formValue.endTime,
        isAvailable: formValue.isAvailable,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('时段已更新。')));
      await _loadTimeSlots();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_readError(error, '更新时段失败。'))));
    } finally {
      if (mounted) {
        setState(() {
          handlingTimeSlotId = 0;
        });
      }
    }
  }

  Future<void> _deleteTimeSlot(TimeSlot slot) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('删除时段'),
          content: Text(
            '确认删除 ${slot.date} ${_trimTime(slot.startTime)}-${_trimTime(slot.endTime)} 吗？',
          ),
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
      handlingTimeSlotId = slot.id;
    });
    try {
      await widget.api.deleteTimeSlot(timeSlotId: slot.id);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('时段已删除。')));
      await _loadTimeSlots();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_readError(error, '删除时段失败。'))));
    } finally {
      if (mounted) {
        setState(() {
          handlingTimeSlotId = 0;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = '${widget.field.fieldType} ${widget.field.number}'.trim();
    return Scaffold(
      appBar: AppBar(title: Text('$title - 时段管理')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: widget.field.isActive ? _createTimeSlot : null,
        icon: const Icon(Icons.add_alarm_outlined),
        label: const Text('新增时段'),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadTimeSlots,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
            children: [
              if (!widget.field.isActive) ...[
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('该场地已停用，不能新增可预约时段。'),
                  ),
                ),
                const SizedBox(height: 12),
              ],
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
                    onPressed: _loadTimeSlots,
                    icon: const Icon(Icons.refresh),
                    label: const Text('重试'),
                  ),
                )
              else if (timeSlots.isEmpty)
                const _MessagePanel(
                  icon: Icons.schedule_outlined,
                  message: '当前还没有时段。',
                )
              else
                for (final slot in timeSlots) ...[
                  _TimeSlotCard(
                    slot: slot,
                    isHandling: handlingTimeSlotId == slot.id,
                    onEdit: handlingTimeSlotId == 0
                        ? () => _editTimeSlot(slot)
                        : null,
                    onDelete: handlingTimeSlotId == 0
                        ? () => _deleteTimeSlot(slot)
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

class _TimeSlotCard extends StatelessWidget {
  const _TimeSlotCard({
    required this.slot,
    required this.isHandling,
    required this.onEdit,
    required this.onDelete,
  });

  final TimeSlot slot;
  final bool isHandling;
  final VoidCallback? onEdit;
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
                    '${slot.date} ${_trimTime(slot.startTime)}-${_trimTime(slot.endTime)}',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Chip(label: Text(slot.isAvailable ? '可预约' : '不可约')),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
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

String _trimTime(String value) {
  if (value.length >= 5) return value.substring(0, 5);
  return value;
}

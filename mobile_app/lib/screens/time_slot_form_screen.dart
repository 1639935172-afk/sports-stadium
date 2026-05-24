import 'package:flutter/material.dart';

import '../models/stadium.dart';

class TimeSlotFormValue {
  const TimeSlotFormValue({
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.isAvailable,
  });

  final String date;
  final String startTime;
  final String endTime;
  final bool isAvailable;
}

class TimeSlotFormScreen extends StatefulWidget {
  const TimeSlotFormScreen({super.key, this.initialSlot});

  final TimeSlot? initialSlot;

  @override
  State<TimeSlotFormScreen> createState() => _TimeSlotFormScreenState();
}

class _TimeSlotFormScreenState extends State<TimeSlotFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _dateController;
  late final TextEditingController _startTimeController;
  late final TextEditingController _endTimeController;
  late bool _isAvailable;

  bool get _isEditing => widget.initialSlot != null;

  @override
  void initState() {
    super.initState();
    final slot = widget.initialSlot;
    _dateController = TextEditingController(text: slot?.date ?? '');
    _startTimeController = TextEditingController(
      text: _trimTime(slot?.startTime ?? ''),
    );
    _endTimeController = TextEditingController(
      text: _trimTime(slot?.endTime ?? ''),
    );
    _isAvailable = slot?.isAvailable ?? true;
  }

  @override
  void dispose() {
    _dateController.dispose();
    _startTimeController.dispose();
    _endTimeController.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.of(context).pop(
      TimeSlotFormValue(
        date: _dateController.text.trim(),
        startTime: _normalizeTime(_startTimeController.text.trim()),
        endTime: _normalizeTime(_endTimeController.text.trim()),
        isAvailable: _isAvailable,
      ),
    );
  }

  Future<void> _pickDate() async {
    final today = DateTime.now();
    final firstDate = _isEditing
        ? DateTime(2024)
        : DateTime(today.year, today.month, today.day);
    final initial = DateTime.tryParse(_dateController.text.trim()) ?? firstDate;
    final picked = await showDatePicker(
      context: context,
      initialDate: initial.isBefore(firstDate) ? firstDate : initial,
      firstDate: firstDate,
      lastDate: DateTime(2100),
    );
    if (picked == null) return;
    _dateController.text =
        '${picked.year.toString().padLeft(4, '0')}-'
        '${picked.month.toString().padLeft(2, '0')}-'
        '${picked.day.toString().padLeft(2, '0')}';
  }

  Future<void> _pickTime(TextEditingController controller) async {
    final current =
        _parseTimeOfDay(controller.text.trim()) ??
        const TimeOfDay(hour: 9, minute: 0);
    final picked = await showTimePicker(context: context, initialTime: current);
    if (picked == null) return;
    controller.text =
        '${picked.hour.toString().padLeft(2, '0')}:'
        '${picked.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        centerTitle: true,
        title: Text(_isEditing ? '编辑时段' : '新增时段'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Form(
                key: _formKey,
                autovalidateMode: AutovalidateMode.onUserInteraction,
                child: Column(
                  children: [
                    TextFormField(
                      controller: _dateController,
                      readOnly: true,
                      onTap: _pickDate,
                      decoration: const InputDecoration(
                        labelText: '开放日期',
                        hintText: 'YYYY-MM-DD',
                        suffixIcon: Icon(Icons.calendar_today_outlined),
                      ),
                      validator: (value) {
                        final text = (value ?? '').trim();
                        if (text.isEmpty) return '请输入日期';
                        final parsed = DateTime.tryParse(text);
                        if (parsed == null) return '请输入合法日期';
                        if (!_isEditing) {
                          final now = DateTime.now();
                          final today = DateTime(now.year, now.month, now.day);
                          if (parsed.isBefore(today)) return '日期不能早于今天';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _startTimeController,
                      readOnly: true,
                      onTap: () => _pickTime(_startTimeController),
                      decoration: const InputDecoration(
                        labelText: '开始时间',
                        hintText: 'HH:MM',
                        suffixIcon: Icon(Icons.schedule_outlined),
                      ),
                      validator: (value) => _validateTime(value),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _endTimeController,
                      readOnly: true,
                      onTap: () => _pickTime(_endTimeController),
                      decoration: const InputDecoration(
                        labelText: '结束时间',
                        hintText: 'HH:MM',
                        suffixIcon: Icon(Icons.schedule_outlined),
                      ),
                      validator: (value) {
                        final error = _validateTime(value);
                        if (error != null) return error;
                        final start = _normalizeTime(
                          _startTimeController.text.trim(),
                        );
                        final end = _normalizeTime((value ?? '').trim());
                        if (start.compareTo(end) >= 0) return '结束时间必须晚于开始时间';
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('可预约'),
                      value: _isAvailable,
                      onChanged: (value) {
                        setState(() {
                          _isAvailable = value;
                        });
                      },
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: _submit,
                        child: Text(_isEditing ? '保存时段' : '创建时段'),
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

String? _validateTime(String? value) {
  final text = (value ?? '').trim();
  if (text.isEmpty) return '请输入时间';
  final parts = text.split(':');
  if (parts.length != 2) return '请输入 HH:MM 格式';
  final hour = int.tryParse(parts[0]);
  final minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) return '请输入 HH:MM 格式';
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) {
    return '请输入合法时间';
  }
  return null;
}

String _normalizeTime(String value) {
  if (value.length == 5) return '$value:00';
  return value;
}

TimeOfDay? _parseTimeOfDay(String value) {
  final parts = value.split(':');
  if (parts.length < 2) return null;
  final hour = int.tryParse(parts[0]);
  final minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) return null;
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return null;
  return TimeOfDay(hour: hour, minute: minute);
}

String _trimTime(String value) {
  if (value.length >= 5) return value.substring(0, 5);
  return value;
}

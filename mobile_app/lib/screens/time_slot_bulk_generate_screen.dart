import 'package:flutter/material.dart';

import '../models/stadium.dart';

class TimeSlotBulkGenerateValue {
  const TimeSlotBulkGenerateValue({
    required this.fieldScope,
    required this.startDate,
    required this.endDate,
    required this.startTime,
    required this.endTime,
    required this.slotMinutes,
    required this.pricePerHour,
    required this.isAvailable,
    required this.skipExisting,
  });

  final String fieldScope;
  final String startDate;
  final String endDate;
  final String startTime;
  final String endTime;
  final int slotMinutes;
  final String pricePerHour;
  final bool isAvailable;
  final bool skipExisting;
}

class TimeSlotBulkGenerateScreen extends StatefulWidget {
  const TimeSlotBulkGenerateScreen({super.key, required this.field});

  final StadiumField field;

  @override
  State<TimeSlotBulkGenerateScreen> createState() =>
      _TimeSlotBulkGenerateScreenState();
}

class _TimeSlotBulkGenerateScreenState
    extends State<TimeSlotBulkGenerateScreen> {
  final _formKey = GlobalKey<FormState>();
  final _startDateController = TextEditingController();
  final _endDateController = TextEditingController();
  final _startTimeController = TextEditingController(text: '09:00');
  final _endTimeController = TextEditingController(text: '18:00');
  final _slotMinutesController = TextEditingController(text: '60');
  late final TextEditingController _priceController;
  var _fieldScope = 'current';
  var _isAvailable = true;
  var _skipExisting = true;

  @override
  void initState() {
    super.initState();
    final today = DateTime.now();
    final todayText = _formatDate(today);
    _startDateController.text = todayText;
    _endDateController.text = todayText;
    _priceController = TextEditingController(text: widget.field.pricePerHour);
  }

  @override
  void dispose() {
    _startDateController.dispose();
    _endDateController.dispose();
    _startTimeController.dispose();
    _endTimeController.dispose();
    _slotMinutesController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.of(context).pop(
      TimeSlotBulkGenerateValue(
        fieldScope: _fieldScope,
        startDate: _startDateController.text.trim(),
        endDate: _endDateController.text.trim(),
        startTime: _normalizeTime(_startTimeController.text.trim()),
        endTime: _normalizeTime(_endTimeController.text.trim()),
        slotMinutes: int.parse(_slotMinutesController.text.trim()),
        pricePerHour: _priceController.text.trim(),
        isAvailable: _isAvailable,
        skipExisting: _skipExisting,
      ),
    );
  }

  Future<void> _pickDate(TextEditingController controller) async {
    final today = DateTime.now();
    final firstDate = DateTime(today.year, today.month, today.day);
    final initial = DateTime.tryParse(controller.text.trim()) ?? firstDate;
    final picked = await showDatePicker(
      context: context,
      initialDate: initial.isBefore(firstDate) ? firstDate : initial,
      firstDate: firstDate,
      lastDate: DateTime(2100),
    );
    if (picked == null) return;
    controller.text = _formatDate(picked);
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
    final title = '${widget.field.fieldType} ${widget.field.number}'.trim();
    return Scaffold(
      appBar: AppBar(centerTitle: true, title: const Text('批量生成时段')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: Form(
                key: _formKey,
                autovalidateMode: AutovalidateMode.onUserInteraction,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      title.isEmpty ? '当前场地' : title,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: _fieldScope,
                      decoration: const InputDecoration(labelText: '选择场地'),
                      items: const [
                        DropdownMenuItem(value: 'current', child: Text('当前场地')),
                        DropdownMenuItem(value: 'all', child: Text('全部启用场地')),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setState(() {
                          _fieldScope = value;
                        });
                      },
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _startDateController,
                      readOnly: true,
                      onTap: () => _pickDate(_startDateController),
                      decoration: const InputDecoration(
                        labelText: '开始日期',
                        suffixIcon: Icon(Icons.calendar_today_outlined),
                      ),
                      validator: (value) =>
                          _validateDate(value, allowPast: false),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _endDateController,
                      readOnly: true,
                      onTap: () => _pickDate(_endDateController),
                      decoration: const InputDecoration(
                        labelText: '结束日期',
                        suffixIcon: Icon(Icons.calendar_today_outlined),
                      ),
                      validator: (value) {
                        final error = _validateDate(value, allowPast: false);
                        if (error != null) return error;
                        final start = DateTime.tryParse(
                          _startDateController.text.trim(),
                        );
                        final end = DateTime.tryParse((value ?? '').trim());
                        if (start != null &&
                            end != null &&
                            end.isBefore(start)) {
                          return '结束日期不能早于开始日期';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _startTimeController,
                            readOnly: true,
                            onTap: () => _pickTime(_startTimeController),
                            decoration: const InputDecoration(
                              labelText: '每日开始时间',
                              suffixIcon: Icon(Icons.schedule_outlined),
                            ),
                            validator: _validateTime,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextFormField(
                            controller: _endTimeController,
                            readOnly: true,
                            onTap: () => _pickTime(_endTimeController),
                            decoration: const InputDecoration(
                              labelText: '每日结束时间',
                              suffixIcon: Icon(Icons.schedule_outlined),
                            ),
                            validator: (value) {
                              final error = _validateTime(value);
                              if (error != null) return error;
                              final start = _normalizeTime(
                                _startTimeController.text.trim(),
                              );
                              final end = _normalizeTime((value ?? '').trim());
                              if (start.compareTo(end) >= 0) {
                                return '结束时间必须晚于开始时间';
                              }
                              return null;
                            },
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _slotMinutesController,
                      decoration: const InputDecoration(
                        labelText: '单个时段长度（分钟）',
                      ),
                      keyboardType: TextInputType.number,
                      validator: (value) {
                        final number = int.tryParse((value ?? '').trim());
                        if (number == null) return '请输入时段长度';
                        if (number < 15 || number > 240) {
                          return '时段长度需在15到240分钟之间';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _priceController,
                      decoration: const InputDecoration(labelText: '每小时价格'),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      validator: (value) {
                        final number = double.tryParse((value ?? '').trim());
                        if (number == null) return '请输入合法价格';
                        if (number < 0) return '价格不能小于0';
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('生成后可预约'),
                      value: _isAvailable,
                      onChanged: (value) {
                        setState(() {
                          _isAvailable = value;
                        });
                      },
                    ),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('跳过已有冲突时段'),
                      value: _skipExisting,
                      onChanged: (value) {
                        setState(() {
                          _skipExisting = value;
                        });
                      },
                    ),
                    const SizedBox(height: 20),
                    FilledButton(
                      onPressed: _submit,
                      child: const Text('批量生成时段'),
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

String? _validateDate(String? value, {required bool allowPast}) {
  final text = (value ?? '').trim();
  if (text.isEmpty) return '请选择日期';
  final parsed = DateTime.tryParse(text);
  if (parsed == null) return '请选择合法日期';
  if (!allowPast) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    if (parsed.isBefore(today)) return '开始日期不能早于今天';
  }
  return null;
}

String? _validateTime(String? value) {
  final text = (value ?? '').trim();
  if (text.isEmpty) return '请选择时间';
  final parts = text.split(':');
  if (parts.length != 2) return '请输入 HH:MM 格式';
  final hour = int.tryParse(parts[0]);
  final minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) return '请输入 HH:MM 格式';
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return '请选择合法时间';
  return null;
}

String _normalizeTime(String value) {
  if (value.length == 5) return '$value:00';
  return value;
}

String _formatDate(DateTime value) {
  return '${value.year.toString().padLeft(4, '0')}-'
      '${value.month.toString().padLeft(2, '0')}-'
      '${value.day.toString().padLeft(2, '0')}';
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

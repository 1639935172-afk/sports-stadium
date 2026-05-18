import 'package:flutter/material.dart';

import '../models/stadium.dart';

class FieldFormValue {
  const FieldFormValue({
    required this.fieldType,
    required this.number,
    required this.isActive,
    required this.pricePerHour,
  });

  final String fieldType;
  final String number;
  final bool isActive;
  final String pricePerHour;
}

class FieldFormScreen extends StatefulWidget {
  const FieldFormScreen({super.key, this.initialField});

  final StadiumField? initialField;

  @override
  State<FieldFormScreen> createState() => _FieldFormScreenState();
}

class _FieldFormScreenState extends State<FieldFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _typeController;
  late final TextEditingController _numberController;
  late final TextEditingController _priceController;
  late bool _isActive;

  bool get _isEditing => widget.initialField != null;

  @override
  void initState() {
    super.initState();
    final field = widget.initialField;
    _typeController = TextEditingController(text: field?.fieldType ?? '');
    _numberController = TextEditingController(text: field?.number ?? '');
    _priceController = TextEditingController(text: field?.pricePerHour ?? '');
    _isActive = field?.isActive ?? true;
  }

  @override
  void dispose() {
    _typeController.dispose();
    _numberController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.of(context).pop(
      FieldFormValue(
        fieldType: _typeController.text.trim(),
        number: _numberController.text.trim(),
        isActive: _isActive,
        pricePerHour: _priceController.text.trim(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_isEditing ? '编辑场地' : '新增场地')),
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
                  controller: _typeController,
                  decoration: const InputDecoration(labelText: '场地类型'),
                  maxLength: 50,
                  textInputAction: TextInputAction.next,
                  validator: (value) =>
                      (value ?? '').trim().isEmpty ? '请输入场地类型' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _numberController,
                  decoration: const InputDecoration(labelText: '场地编号'),
                  maxLength: 50,
                  textInputAction: TextInputAction.next,
                  validator: (value) =>
                      (value ?? '').trim().isEmpty ? '请输入场地编号' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _priceController,
                  decoration: const InputDecoration(labelText: '预约单价/小时'),
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  textInputAction: TextInputAction.done,
                  onFieldSubmitted: (_) => _submit(),
                  validator: (value) {
                    final text = (value ?? '').trim();
                    if (text.isEmpty) return '请输入价格';
                    if (double.tryParse(text) == null) return '请输入合法价格';
                    if (double.parse(text) <= 0) return '价格必须大于0';
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('启用场地'),
                  value: _isActive,
                  onChanged: (value) {
                    setState(() {
                      _isActive = value;
                    });
                  },
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: _submit,
                    child: Text(_isEditing ? '保存场地' : '创建场地'),
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

import 'package:flutter/material.dart';

import '../models/stadium.dart';

class StadiumFormValue {
  const StadiumFormValue({
    required this.name,
    required this.address,
    required this.phoneNumber,
    required this.information,
  });

  final String name;
  final String address;
  final String phoneNumber;
  final String information;
}

class StadiumFormScreen extends StatefulWidget {
  const StadiumFormScreen({super.key, this.initialStadium});

  final Stadium? initialStadium;

  @override
  State<StadiumFormScreen> createState() => _StadiumFormScreenState();
}

class _StadiumFormScreenState extends State<StadiumFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _addressController;
  late final TextEditingController _phoneController;
  late final TextEditingController _informationController;

  bool get _isEditing => widget.initialStadium != null;

  @override
  void initState() {
    super.initState();
    final initial = widget.initialStadium;
    _nameController = TextEditingController(text: initial?.name ?? '');
    _addressController = TextEditingController(text: initial?.address ?? '');
    _phoneController = TextEditingController(text: initial?.phoneNumber ?? '');
    _informationController = TextEditingController(
      text: initial?.information ?? '',
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _addressController.dispose();
    _phoneController.dispose();
    _informationController.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.of(context).pop(
      StadiumFormValue(
        name: _nameController.text.trim(),
        address: _addressController.text.trim(),
        phoneNumber: _phoneController.text.trim(),
        information: _informationController.text.trim(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_isEditing ? '编辑场馆' : '新增场馆')),
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
                  controller: _nameController,
                  decoration: const InputDecoration(labelText: '场馆名称'),
                  maxLength: 100,
                  textInputAction: TextInputAction.next,
                  validator: (value) {
                    if ((value ?? '').trim().isEmpty) return '请输入场馆名称';
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _addressController,
                  decoration: const InputDecoration(labelText: '场馆地址'),
                  maxLength: 255,
                  textInputAction: TextInputAction.next,
                  validator: (value) {
                    if ((value ?? '').trim().isEmpty) return '请输入场馆地址';
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _phoneController,
                  decoration: const InputDecoration(labelText: '联系电话'),
                  maxLength: 11,
                  keyboardType: TextInputType.phone,
                  textInputAction: TextInputAction.next,
                  validator: (value) {
                    final text = (value ?? '').trim();
                    if (text.isEmpty) return '请输入联系电话';
                    if (text.length != 11 || int.tryParse(text) == null) {
                      return '请输入11位手机号';
                    }
                    if (!text.startsWith('1')) {
                      return '请输入11位手机号';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _informationController,
                  decoration: const InputDecoration(labelText: '场馆简介'),
                  minLines: 4,
                  maxLines: 6,
                  textInputAction: TextInputAction.newline,
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: _submit,
                    child: Text(_isEditing ? '保存并重新提交审核' : '提交审核'),
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

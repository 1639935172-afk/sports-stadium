class Stadium {
  const Stadium({
    required this.id,
    required this.name,
    required this.address,
    required this.phoneNumber,
    required this.information,
    this.auditStatus = '',
    this.isOpen = false,
    this.deletionRequested = false,
    this.ownerNickname = '',
    this.ownerPhoneNumber = '',
    this.createdAt = '',
    this.updatedAt = '',
  });

  final int id;
  final String name;
  final String address;
  final String phoneNumber;
  final String information;
  final String auditStatus;
  final bool isOpen;
  final bool deletionRequested;
  final String ownerNickname;
  final String ownerPhoneNumber;
  final String createdAt;
  final String updatedAt;

  factory Stadium.fromJson(Map<String, dynamic> json) {
    return Stadium(
      id: json['id'] as int,
      name: json['name'] as String? ?? '',
      address: json['address'] as String? ?? '',
      phoneNumber: json['phone_number'] as String? ?? '',
      information: json['information'] as String? ?? '',
      auditStatus: json['audit_status'] as String? ?? '',
      isOpen: json['is_open'] as bool? ?? false,
      deletionRequested: json['deletion_requested'] as bool? ?? false,
      ownerNickname: json['owner_nickname'] as String? ?? '',
      ownerPhoneNumber: json['owner_phone_number'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }
}

class StadiumDetail extends Stadium {
  const StadiumDetail({
    required super.id,
    required super.name,
    required super.address,
    required super.phoneNumber,
    required super.information,
    required this.fields,
  });

  final List<StadiumField> fields;

  factory StadiumDetail.fromJson(Map<String, dynamic> json) {
    final fieldsJson = json['fields'] as List<dynamic>? ?? <dynamic>[];
    return StadiumDetail(
      id: json['id'] as int,
      name: json['name'] as String? ?? '',
      address: json['address'] as String? ?? '',
      phoneNumber: json['phone_number'] as String? ?? '',
      information: json['information'] as String? ?? '',
      fields: fieldsJson
          .map((item) => StadiumField.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}

class StadiumField {
  const StadiumField({
    required this.id,
    this.stadium = 0,
    this.stadiumName = '',
    required this.fieldType,
    required this.number,
    this.isActive = true,
    required this.pricePerHour,
    required this.timeSlots,
  });

  final int id;
  final int stadium;
  final String stadiumName;
  final String fieldType;
  final String number;
  final bool isActive;
  final String pricePerHour;
  final List<TimeSlot> timeSlots;

  factory StadiumField.fromJson(Map<String, dynamic> json) {
    final slotsJson = json['time_slots'] as List<dynamic>? ?? <dynamic>[];
    return StadiumField(
      id: json['id'] as int,
      stadium: json['stadium'] as int? ?? 0,
      stadiumName: json['stadium_name'] as String? ?? '',
      fieldType: json['field_type'] as String? ?? '',
      number: json['number'] as String? ?? '',
      isActive: json['is_active'] as bool? ?? true,
      pricePerHour: json['price_per_hour']?.toString() ?? '',
      timeSlots: slotsJson
          .map((item) => TimeSlot.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}

class TimeSlot {
  const TimeSlot({
    required this.id,
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.isAvailable,
  });

  final int id;
  final String date;
  final String startTime;
  final String endTime;
  final bool isAvailable;

  factory TimeSlot.fromJson(Map<String, dynamic> json) {
    return TimeSlot(
      id: json['id'] as int,
      date: json['date'] as String? ?? '',
      startTime: json['start_time'] as String? ?? '',
      endTime: json['end_time'] as String? ?? '',
      isAvailable: json['is_available'] as bool? ?? false,
    );
  }
}

class TimeSlotBulkGenerateResult {
  const TimeSlotBulkGenerateResult({
    required this.createdCount,
    required this.skippedCount,
    required this.failedCount,
  });

  final int createdCount;
  final int skippedCount;
  final int failedCount;

  factory TimeSlotBulkGenerateResult.fromJson(Map<String, dynamic> json) {
    return TimeSlotBulkGenerateResult(
      createdCount: json['created_count'] as int? ?? 0,
      skippedCount: json['skipped_count'] as int? ?? 0,
      failedCount: json['failed_count'] as int? ?? 0,
    );
  }
}

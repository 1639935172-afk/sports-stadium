class Stadium {
  const Stadium({
    required this.id,
    required this.name,
    required this.address,
    required this.phoneNumber,
    required this.information,
  });

  final int id;
  final String name;
  final String address;
  final String phoneNumber;
  final String information;

  factory Stadium.fromJson(Map<String, dynamic> json) {
    return Stadium(
      id: json['id'] as int,
      name: json['name'] as String? ?? '',
      address: json['address'] as String? ?? '',
      phoneNumber: json['phone_number'] as String? ?? '',
      information: json['information'] as String? ?? '',
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
    required this.fieldType,
    required this.number,
    required this.pricePerHour,
    required this.timeSlots,
  });

  final int id;
  final String fieldType;
  final String number;
  final String pricePerHour;
  final List<TimeSlot> timeSlots;

  factory StadiumField.fromJson(Map<String, dynamic> json) {
    final slotsJson = json['time_slots'] as List<dynamic>? ?? <dynamic>[];
    return StadiumField(
      id: json['id'] as int,
      fieldType: json['field_type'] as String? ?? '',
      number: json['number'] as String? ?? '',
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

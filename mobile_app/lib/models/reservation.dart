class Reservation {
  const Reservation({
    required this.id,
    required this.timeSlot,
    required this.status,
    required this.stadiumName,
    required this.fieldNumber,
    required this.fieldType,
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.isExpired,
    required this.paymentStatus,
    required this.paymentAmount,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final int timeSlot;
  final String status;
  final String stadiumName;
  final String fieldNumber;
  final String fieldType;
  final String date;
  final String startTime;
  final String endTime;
  final bool isExpired;
  final String paymentStatus;
  final String paymentAmount;
  final String createdAt;
  final String updatedAt;

  factory Reservation.fromJson(Map<String, dynamic> json) {
    return Reservation(
      id: json['id'] as int,
      timeSlot: json['time_slot'] as int? ?? 0,
      status: json['status'] as String? ?? '',
      stadiumName: json['stadium_name'] as String? ?? '',
      fieldNumber: json['field_number'] as String? ?? '',
      fieldType: json['field_type'] as String? ?? '',
      date: json['date'] as String? ?? '',
      startTime: json['start_time'] as String? ?? '',
      endTime: json['end_time'] as String? ?? '',
      isExpired: json['is_expired'] as bool? ?? false,
      paymentStatus: json['payment_status'] as String? ?? '',
      paymentAmount: json['payment_amount'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }
}

class ReservationCreateResult {
  const ReservationCreateResult({
    required this.id,
    required this.timeSlot,
    required this.status,
    required this.paymentStatus,
    required this.paymentAmount,
    required this.createdAt,
  });

  final int id;
  final int timeSlot;
  final String status;
  final String paymentStatus;
  final String paymentAmount;
  final String createdAt;

  factory ReservationCreateResult.fromJson(Map<String, dynamic> json) {
    return ReservationCreateResult(
      id: json['id'] as int,
      timeSlot: json['time_slot'] as int? ?? 0,
      status: json['status'] as String? ?? '',
      paymentStatus: json['payment_status'] as String? ?? '',
      paymentAmount: json['payment_amount'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

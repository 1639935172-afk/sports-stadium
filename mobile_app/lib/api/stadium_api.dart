import '../models/stadium.dart';
import 'api_client.dart';

class StadiumAuditActionResult {
  const StadiumAuditActionResult({
    required this.action,
    this.stadium,
    this.detail = '',
  });

  final String action;
  final Stadium? stadium;
  final String detail;
}

class StadiumApi {
  const StadiumApi(this.client);

  final ApiClient client;

  Future<List<Stadium>> list({String query = ''}) async {
    final response = await client.dio.get<List<dynamic>>(
      '/stadiums/',
      queryParameters: query.trim().isEmpty ? null : {'q': query.trim()},
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => Stadium.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<StadiumDetail> detail(int id) async {
    final response = await client.dio.get<Map<String, dynamic>>(
      '/stadiums/$id/',
    );
    return StadiumDetail.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<List<Stadium>> adminPending() async {
    final response = await client.dio.get<List<dynamic>>(
      '/stadiums/admin/pending/',
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => Stadium.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<Stadium>> mine() async {
    final response = await client.dio.get<List<dynamic>>('/stadiums/mine/');
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => Stadium.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<Stadium> createManaged({
    required String name,
    required String address,
    required String phoneNumber,
    required String information,
  }) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/stadiums/mine/',
      data: {
        'name': name,
        'address': address,
        'phone_number': phoneNumber,
        'information': information,
      },
    );
    return Stadium.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<Stadium> updateManaged({
    required int stadiumId,
    required String name,
    required String address,
    required String phoneNumber,
    required String information,
  }) async {
    final response = await client.dio.patch<Map<String, dynamic>>(
      '/stadiums/mine/$stadiumId/',
      data: {
        'name': name,
        'address': address,
        'phone_number': phoneNumber,
        'information': information,
      },
    );
    return Stadium.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<Stadium> requestDeletion({required int stadiumId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/stadiums/mine/$stadiumId/delete-request/',
    );
    return Stadium.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<List<StadiumField>> fields({required int stadiumId}) async {
    final response = await client.dio.get<List<dynamic>>(
      '/stadiums/mine/$stadiumId/fields/',
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => StadiumField.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<StadiumField> createField({
    required int stadiumId,
    required String fieldType,
    required String number,
    required bool isActive,
    required String pricePerHour,
  }) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/stadiums/mine/$stadiumId/fields/',
      data: {
        'field_type': fieldType,
        'number': number,
        'is_active': isActive,
        'price_per_hour': pricePerHour,
      },
    );
    return StadiumField.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<StadiumField> updateField({
    required int fieldId,
    required String fieldType,
    required String number,
    required bool isActive,
    required String pricePerHour,
  }) async {
    final response = await client.dio.patch<Map<String, dynamic>>(
      '/fields/$fieldId/',
      data: {
        'field_type': fieldType,
        'number': number,
        'is_active': isActive,
        'price_per_hour': pricePerHour,
      },
    );
    return StadiumField.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<StadiumField> disableField({required int fieldId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/fields/$fieldId/disable/',
    );
    return StadiumField.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<void> deleteField({required int fieldId}) async {
    await client.dio.delete<void>('/fields/$fieldId/');
  }

  Future<List<TimeSlot>> timeSlots({required int fieldId}) async {
    final response = await client.dio.get<List<dynamic>>(
      '/fields/$fieldId/time-slots/',
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => TimeSlot.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<TimeSlot> createTimeSlot({
    required int fieldId,
    required String date,
    required String startTime,
    required String endTime,
    required bool isAvailable,
  }) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/fields/$fieldId/time-slots/',
      data: {
        'date': date,
        'start_time': startTime,
        'end_time': endTime,
        'is_available': isAvailable,
      },
    );
    return TimeSlot.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<TimeSlot> updateTimeSlot({
    required int timeSlotId,
    required String date,
    required String startTime,
    required String endTime,
    required bool isAvailable,
  }) async {
    final response = await client.dio.patch<Map<String, dynamic>>(
      '/time-slots/$timeSlotId/',
      data: {
        'date': date,
        'start_time': startTime,
        'end_time': endTime,
        'is_available': isAvailable,
      },
    );
    return TimeSlot.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<void> deleteTimeSlot({required int timeSlotId}) async {
    await client.dio.delete<void>('/time-slots/$timeSlotId/');
  }

  Future<StadiumAuditActionResult> approve({required int stadiumId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/stadiums/$stadiumId/approve/',
    );
    final data = response.data ?? <String, dynamic>{};
    if (data['action'] == 'deleted') {
      return StadiumAuditActionResult(
        action: 'deleted',
        detail: data['detail'] as String? ?? '',
      );
    }
    return StadiumAuditActionResult(
      action: 'approved',
      stadium: Stadium.fromJson(data),
    );
  }

  Future<StadiumAuditActionResult> reject({required int stadiumId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/stadiums/$stadiumId/reject/',
    );
    return StadiumAuditActionResult(
      action: 'rejected',
      stadium: Stadium.fromJson(response.data ?? <String, dynamic>{}),
    );
  }
}

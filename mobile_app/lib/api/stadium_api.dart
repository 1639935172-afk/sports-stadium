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

  /// GET /stadiums/?q=...
  ///
  /// 首页场馆列表和搜索使用这个接口；queryParameters 会被 Dio 拼到 URL 查询串。
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

  /// GET `/stadiums/<id>/`
  ///
  /// 场馆详情页使用这个接口。后端返回场馆、场地、可预约时段的嵌套 JSON，
  /// 这里再转换成 StadiumDetail / StadiumField / TimeSlot 模型。
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

  /// 场馆管理员侧接口：这些 `/stadiums/mine/...` 请求都依赖 JWT 里的用户身份。
  /// 后端会用 request.user 限制只能管理自己名下的场馆、场地和时段。
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

  Future<TimeSlotBulkGenerateResult> bulkGenerateTimeSlots({
    required int fieldId,
    required String fieldScope,
    required String startDate,
    required String endDate,
    required String startTime,
    required String endTime,
    required int slotMinutes,
    required String pricePerHour,
    required bool isAvailable,
    required bool skipExisting,
  }) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/fields/$fieldId/time-slots/generate/',
      data: {
        'field_scope': fieldScope,
        'start_date': startDate,
        'end_date': endDate,
        'start_time': startTime,
        'end_time': endTime,
        'slot_minutes': slotMinutes,
        'price_per_hour': pricePerHour,
        'is_available': isAvailable,
        'skip_existing': skipExisting,
      },
    );
    return TimeSlotBulkGenerateResult.fromJson(
      response.data ?? <String, dynamic>{},
    );
  }

  Future<int> clearExpiredTimeSlots({required int fieldId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/fields/$fieldId/time-slots/clear-expired/',
    );
    final data = response.data ?? <String, dynamic>{};
    return data['deleted_count'] as int? ?? 0;
  }

  /// POST `/stadiums/<id>/approve/`
  ///
  /// 同一个审核通过接口有两种后端返回：
  /// 1. 普通场馆审核通过时返回 Stadium JSON；
  /// 2. 删除申请审核通过时返回 `{action: deleted}`，App 需要单独处理。
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

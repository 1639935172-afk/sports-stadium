import '../models/reservation.dart';
import 'api_client.dart';

class ReservationApi {
  const ReservationApi(this.client);

  final ApiClient client;

  /// POST /reservations/
  ///
  /// 用户点击“预约”后只提交 time_slot id。后端会再次检查时段是否可约、
  /// 是否冲突、是否过期，并创建 awaiting_payment 状态的预约和支付单。
  Future<ReservationCreateResult> create({required int timeSlotId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/reservations/',
      data: {'time_slot': timeSlotId},
    );
    return ReservationCreateResult.fromJson(
      response.data ?? <String, dynamic>{},
    );
  }

  /// GET /reservations/mine/
  ///
  /// “我的预约”页面使用；后端会返回当前普通用户的全部预约，
  /// 包括支付状态、支付金额和 is_expired 派生状态。
  Future<List<Reservation>> mine() async {
    final response = await client.dio.get<List<dynamic>>('/reservations/mine/');
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => Reservation.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<Reservation>> adminPending() async {
    final response = await client.dio.get<List<dynamic>>(
      '/reservations/admin/pending/',
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => Reservation.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<Reservation> cancel({required int reservationId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/reservations/$reservationId/cancel/',
    );
    return Reservation.fromJson(response.data ?? <String, dynamic>{});
  }

  /// POST `/reservations/<id>/pay/`
  ///
  /// 当前项目是模拟支付：点击“去支付”后调用该接口，
  /// 后端把支付单标记为 paid，并把预约推进到 pending，等待场馆管理员审核。
  Future<Reservation> pay({required int reservationId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/reservations/$reservationId/pay/',
    );
    return Reservation.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<Reservation> paymentFail({required int reservationId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/reservations/$reservationId/payment-fail/',
    );
    return Reservation.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<Reservation> approve({required int reservationId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/reservations/$reservationId/approve/',
    );
    return Reservation.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<Reservation> reject({required int reservationId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/reservations/$reservationId/reject/',
    );
    return Reservation.fromJson(response.data ?? <String, dynamic>{});
  }
}

import '../models/reservation.dart';
import 'api_client.dart';

class ReservationApi {
  const ReservationApi(this.client);

  final ApiClient client;

  Future<ReservationCreateResult> create({required int timeSlotId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/reservations/',
      data: {'time_slot': timeSlotId},
    );
    return ReservationCreateResult.fromJson(
      response.data ?? <String, dynamic>{},
    );
  }

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

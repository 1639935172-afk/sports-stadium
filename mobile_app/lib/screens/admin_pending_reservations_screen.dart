import 'package:flutter/material.dart';

import '../api/reservation_api.dart';
import '../models/reservation.dart';
import '../widgets/app_feedback.dart';

class AdminPendingReservationsScreen extends StatefulWidget {
  const AdminPendingReservationsScreen({super.key, required this.api});

  final ReservationApi api;

  @override
  State<AdminPendingReservationsScreen> createState() =>
      _AdminPendingReservationsScreenState();
}

class _AdminPendingReservationsScreenState
    extends State<AdminPendingReservationsScreen> {
  var reservations = <Reservation>[];
  var isLoading = true;
  var handlingReservationId = 0;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadReservations();
  }

  Future<void> _loadReservations() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final result = await widget.api.adminPending();
      if (!mounted) return;
      setState(() {
        reservations = result;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载待审核预约，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _handleReservation(Reservation reservation, bool approve) async {
    final actionLabel = approve ? '通过' : '驳回';
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('$actionLabel预约'),
          content: Text(
            '确认$actionLabel ${reservation.stadiumName} '
            '${reservation.date} ${_trimSeconds(reservation.startTime)}-${_trimSeconds(reservation.endTime)} 的预约？',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: Text('确认$actionLabel'),
            ),
          ],
        );
      },
    );

    if (confirmed != true) return;

    setState(() {
      handlingReservationId = reservation.id;
    });

    try {
      if (approve) {
        await widget.api.approve(reservationId: reservation.id);
      } else {
        await widget.api.reject(reservationId: reservation.id);
      }
      if (!mounted) return;
      AppFeedback.showMessage(context, '预约已${approve ? '通过' : '驳回'}。');
      await _loadReservations();
    } catch (_) {
      if (!mounted) return;
      AppFeedback.showMessage(
        context,
        '${approve ? '通过' : '驳回'}预约失败，请稍后重试。',
        isError: true,
      );
    } finally {
      if (mounted) {
        setState(() {
          handlingReservationId = 0;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('预约审核')),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadReservations,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            children: [
              if (isLoading)
                const AppPageLoading()
              else if (errorMessage != null)
                AppMessagePanel(
                  icon: Icons.cloud_off,
                  message: errorMessage!,
                  action: TextButton.icon(
                    onPressed: _loadReservations,
                    icon: const Icon(Icons.refresh),
                    label: const Text('重试'),
                  ),
                )
              else if (reservations.isEmpty)
                const AppMessagePanel(
                  icon: Icons.event_available_outlined,
                  message: '当前没有待审核预约。',
                )
              else
                for (final reservation in reservations) ...[
                  _ReservationCard(
                    reservation: reservation,
                    isHandling: handlingReservationId == reservation.id,
                    onApprove: handlingReservationId == 0
                        ? () => _handleReservation(reservation, true)
                        : null,
                    onReject: handlingReservationId == 0
                        ? () => _handleReservation(reservation, false)
                        : null,
                  ),
                  const SizedBox(height: 12),
                ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ReservationCard extends StatelessWidget {
  const _ReservationCard({
    required this.reservation,
    required this.isHandling,
    required this.onApprove,
    required this.onReject,
  });

  final Reservation reservation;
  final bool isHandling;
  final VoidCallback? onApprove;
  final VoidCallback? onReject;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              reservation.stadiumName,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 10),
            _InfoRow(
              label: '场地',
              value: '${reservation.fieldType} ${reservation.fieldNumber}',
            ),
            _InfoRow(
              label: '时间',
              value:
                  '${reservation.date} ${_trimSeconds(reservation.startTime)}-${_trimSeconds(reservation.endTime)}',
            ),
            _InfoRow(label: '状态', value: _statusLabel(reservation.status)),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: onApprove,
                    icon: isHandling
                        ? const AppLoadingIcon()
                        : const Icon(Icons.check_circle_outline),
                    label: const Text('通过'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: onReject,
                    icon: const Icon(Icons.cancel_outlined),
                    label: const Text('驳回'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 48, child: Text(label)),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

String _trimSeconds(String value) {
  if (value.length >= 5) return value.substring(0, 5);
  return value;
}

String _statusLabel(String status) {
  return switch (status) {
    'pending' => '待审核',
    'approved' => '已通过',
    'rejected' => '已驳回',
    'cancelled' => '已取消',
    _ => status,
  };
}

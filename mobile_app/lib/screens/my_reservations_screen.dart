import 'package:flutter/material.dart';

import '../api/reservation_api.dart';
import '../models/reservation.dart';
import '../widgets/app_feedback.dart';

class MyReservationsScreen extends StatefulWidget {
  const MyReservationsScreen({super.key, required this.api});

  final ReservationApi api;

  @override
  State<MyReservationsScreen> createState() => _MyReservationsScreenState();
}

class _MyReservationsScreenState extends State<MyReservationsScreen> {
  var reservations = <Reservation>[];
  var isLoading = true;
  var cancellingReservationId = 0;
  var payingReservationId = 0;
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
      final result = await widget.api.mine();
      if (!mounted) return;
      setState(() {
        reservations = result;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载我的预约，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _confirmCancel(Reservation reservation) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('取消预约'),
          content: Text(
            '确认取消 ${reservation.stadiumName}，'
            '${reservation.date} ${_trimSeconds(reservation.startTime)}-${_trimSeconds(reservation.endTime)} 的预约？',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('保留预约'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('确认取消'),
            ),
          ],
        );
      },
    );

    if (confirmed == true) {
      await _cancelReservation(reservation.id);
    }
  }

  Future<void> _cancelReservation(int reservationId) async {
    setState(() {
      cancellingReservationId = reservationId;
    });

    try {
      await widget.api.cancel(reservationId: reservationId);
      if (!mounted) return;
      AppFeedback.showMessage(context, '预约已取消。');
      await _loadReservations();
    } catch (_) {
      if (!mounted) return;
      AppFeedback.showMessage(context, '取消预约失败，请稍后重试。', isError: true);
    } finally {
      if (mounted) {
        setState(() {
          cancellingReservationId = 0;
        });
      }
    }
  }

  Future<void> _payReservation(Reservation reservation) async {
    setState(() {
      payingReservationId = reservation.id;
    });

    try {
      await widget.api.pay(reservationId: reservation.id);
      if (!mounted) return;
      AppFeedback.showMessage(context, '支付成功，预约已进入待审核。');
      await _loadReservations();
    } catch (_) {
      if (!mounted) return;
      AppFeedback.showMessage(context, '支付失败，请稍后重试。', isError: true);
    } finally {
      if (mounted) {
        setState(() {
          payingReservationId = 0;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(centerTitle: true, title: const Text('我的预约')),
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
                  icon: Icons.event_busy,
                  message: '暂无预约记录。',
                )
              else
                for (final reservation in reservations) ...[
                  _ReservationCard(
                    reservation: reservation,
                    isCancelling: cancellingReservationId == reservation.id,
                    isPaying: payingReservationId == reservation.id,
                    canPay:
                        payingReservationId == 0 &&
                        reservation.status == 'awaiting_payment' &&
                        !reservation.isExpired,
                    canCancel:
                        cancellingReservationId == 0 &&
                        payingReservationId == 0 &&
                        _canCancel(reservation),
                    onPay: () => _payReservation(reservation),
                    onCancel: () => _confirmCancel(reservation),
                  ),
                  const SizedBox(height: 12),
                ],
            ],
          ),
        ),
      ),
    );
  }

  bool _canCancel(Reservation reservation) {
    return !reservation.isExpired &&
        (reservation.status == 'awaiting_payment' ||
            reservation.status == 'pending' ||
            reservation.status == 'approved');
  }
}

class _ReservationCard extends StatelessWidget {
  const _ReservationCard({
    required this.reservation,
    required this.isCancelling,
    required this.isPaying,
    required this.canPay,
    required this.canCancel,
    required this.onPay,
    required this.onCancel,
  });

  final Reservation reservation;
  final bool isCancelling;
  final bool isPaying;
  final bool canPay;
  final bool canCancel;
  final VoidCallback onPay;
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    reservation.stadiumName,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                _StatusBadge(
                  status: reservation.status,
                  isExpired: reservation.isExpired,
                ),
              ],
            ),
            const SizedBox(height: 10),
            _IconText(
              icon: Icons.sports_basketball_outlined,
              text: '${reservation.fieldType} ${reservation.fieldNumber}',
            ),
            _IconText(
              icon: Icons.schedule,
              text:
                  '${reservation.date} ${_trimSeconds(reservation.startTime)}-${_trimSeconds(reservation.endTime)}',
            ),
            if (reservation.paymentStatus.isNotEmpty)
              _IconText(
                icon: Icons.payments_outlined,
                text:
                    '${_paymentStatusLabel(reservation.paymentStatus)} ${reservation.paymentAmount.isEmpty ? '' : '￥${reservation.paymentAmount}'}',
              ),
            if (reservation.status == 'awaiting_payment' &&
                !reservation.isExpired) ...[
              const SizedBox(height: 10),
              Align(
                alignment: Alignment.centerRight,
                child: FilledButton.icon(
                  onPressed: canPay ? onPay : null,
                  icon: isPaying
                      ? const AppLoadingIcon()
                      : const Icon(Icons.payments_outlined),
                  label: Text(isPaying ? '支付中' : '去支付'),
                ),
              ),
            ],
            if (!reservation.isExpired &&
                (reservation.status == 'awaiting_payment' ||
                    reservation.status == 'pending' ||
                    reservation.status == 'approved')) ...[
              const SizedBox(height: 10),
              Align(
                alignment: Alignment.centerRight,
                child: OutlinedButton.icon(
                  onPressed: canCancel ? onCancel : null,
                  icon: isCancelling
                      ? const AppLoadingIcon()
                      : const Icon(Icons.event_busy),
                  label: Text(isCancelling ? '取消中' : '取消预约'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status, required this.isExpired});

  final String status;
  final bool isExpired;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    if (isExpired && status != 'cancelled' && status != 'rejected') {
      return Chip(
        label: const Text('已过期'),
        visualDensity: VisualDensity.compact,
        side: BorderSide(color: colorScheme.outline),
        labelStyle: TextStyle(color: colorScheme.outline),
      );
    }
    final (label, color) = switch (status) {
      'awaiting_payment' => ('待支付', colorScheme.tertiary),
      'pending' => ('待审核', colorScheme.primary),
      'approved' => ('已通过', Colors.green),
      'rejected' => ('已驳回', colorScheme.error),
      'cancelled' => ('已取消', colorScheme.outline),
      'payment_failed' => ('支付失败', colorScheme.error),
      _ => (status, colorScheme.outline),
    };

    return Chip(
      label: Text(label),
      visualDensity: VisualDensity.compact,
      side: BorderSide(color: color),
      labelStyle: TextStyle(color: color),
    );
  }
}

class _IconText extends StatelessWidget {
  const _IconText({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18),
          const SizedBox(width: 8),
          Expanded(child: Text(text.isEmpty ? '未填写' : text)),
        ],
      ),
    );
  }
}

String _trimSeconds(String value) {
  if (value.length >= 5) return value.substring(0, 5);
  return value;
}

String _paymentStatusLabel(String status) {
  return switch (status) {
    'unpaid' => '待支付',
    'paid' => '已支付',
    'failed' => '支付失败',
    'closed' => '已关闭',
    'refunded' => '已退款',
    _ => status,
  };
}

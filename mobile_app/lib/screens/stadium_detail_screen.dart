import 'package:flutter/material.dart';

import '../api/comment_api.dart';
import '../api/reservation_api.dart';
import '../api/stadium_api.dart';
import '../models/comment.dart';
import '../models/stadium.dart';

class StadiumDetailScreen extends StatefulWidget {
  const StadiumDetailScreen({
    super.key,
    required this.stadiumId,
    required this.initialName,
    required this.api,
    required this.reservationApi,
    required this.commentApi,
    required this.canReserve,
    required this.canSubmitComment,
  });

  final int stadiumId;
  final String initialName;
  final StadiumApi api;
  final ReservationApi reservationApi;
  final CommentApi commentApi;
  final bool canReserve;
  final bool canSubmitComment;

  @override
  State<StadiumDetailScreen> createState() => _StadiumDetailScreenState();
}

class _StadiumDetailScreenState extends State<StadiumDetailScreen> {
  final commentController = TextEditingController();
  StadiumDetail? stadium;
  var comments = <StadiumComment>[];
  var isLoading = true;
  var submittingSlotId = 0;
  var isSubmittingComment = false;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  @override
  void dispose() {
    commentController.dispose();
    super.dispose();
  }

  Future<void> _confirmReservation(StadiumField field, TimeSlot slot) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('提交预约'),
          content: Text(
            '确认预约 ${field.fieldType} ${field.number}，'
            '${slot.date} ${_trimSeconds(slot.startTime)}-${_trimSeconds(slot.endTime)}？',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('确认预约'),
            ),
          ],
        );
      },
    );

    if (confirmed == true) {
      await _submitReservation(slot.id);
    }
  }

  Future<void> _submitReservation(int timeSlotId) async {
    setState(() {
      submittingSlotId = timeSlotId;
    });

    try {
      await widget.reservationApi.create(timeSlotId: timeSlotId);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('预约已提交，等待场馆管理员审核。')));
      await _loadDetail();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('预约提交失败，请确认时段仍可预约。')));
    } finally {
      if (mounted) {
        setState(() {
          submittingSlotId = 0;
        });
      }
    }
  }

  Future<void> _loadDetail() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final detailResult = await widget.api.detail(widget.stadiumId);
      final commentResult = await widget.commentApi.listForStadium(
        widget.stadiumId,
      );
      if (!mounted) return;
      setState(() {
        stadium = detailResult;
        comments = commentResult;
        isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        isLoading = false;
        errorMessage = '无法加载场馆详情，请确认 Django 服务已启动。';
      });
    }
  }

  Future<void> _submitComment() async {
    final content = commentController.text.trim();
    if (content.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('请输入评论内容。')));
      return;
    }

    setState(() {
      isSubmittingComment = true;
    });

    try {
      await widget.commentApi.create(
        stadiumId: widget.stadiumId,
        content: content,
      );
      if (!mounted) return;
      commentController.clear();
      FocusScope.of(context).unfocus();
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('评论已提交，等待系统管理员审核。')));
      await _loadDetail();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('评论提交失败，请稍后重试。')));
    } finally {
      if (mounted) {
        setState(() {
          isSubmittingComment = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(stadium?.name ?? widget.initialName)),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadDetail,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            children: [
              if (isLoading)
                const Padding(
                  padding: EdgeInsets.only(top: 120),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (errorMessage != null)
                _MessagePanel(
                  icon: Icons.cloud_off,
                  message: errorMessage!,
                  action: TextButton.icon(
                    onPressed: _loadDetail,
                    icon: const Icon(Icons.refresh),
                    label: const Text('重试'),
                  ),
                )
              else if (stadium != null) ...[
                _StadiumInfoCard(stadium: stadium!),
                const SizedBox(height: 16),
                Text(
                  '场地与可预约时段',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 10),
                if (stadium!.fields.isNotEmpty)
                  for (final field in stadium!.fields) ...[
                    _FieldCard(
                      field: field,
                      submittingSlotId: submittingSlotId,
                      canReserve: widget.canReserve,
                      onReserve: (slot) => _confirmReservation(field, slot),
                    ),
                    const SizedBox(height: 12),
                  ]
                else
                  const _MessagePanel(
                    icon: Icons.event_busy,
                    message: '暂无可预约场地。',
                  ),
                const SizedBox(height: 16),
                Text('场馆评论', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 10),
                if (widget.canSubmitComment) ...[
                  _CommentComposer(
                    controller: commentController,
                    isSubmitting: isSubmittingComment,
                    onSubmit: _submitComment,
                  ),
                  const SizedBox(height: 12),
                ],
                if (comments.isEmpty)
                  const _MessagePanel(
                    icon: Icons.rate_review_outlined,
                    message: '暂无已审核评论。',
                  )
                else
                  for (final comment in comments) ...[
                    _CommentCard(comment: comment),
                    const SizedBox(height: 12),
                  ],
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _CommentComposer extends StatelessWidget {
  const _CommentComposer({
    required this.controller,
    required this.isSubmitting,
    required this.onSubmit,
  });

  final TextEditingController controller;
  final bool isSubmitting;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: controller,
              minLines: 3,
              maxLines: 5,
              textInputAction: TextInputAction.newline,
              decoration: const InputDecoration(
                labelText: '发表评论',
                hintText: '写下你的场馆体验',
              ),
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                onPressed: isSubmitting ? null : onSubmit,
                icon: isSubmitting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send),
                label: Text(isSubmitting ? '提交中' : '提交评论'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CommentCard extends StatelessWidget {
  const _CommentCard({required this.comment});

  final StadiumComment comment;

  @override
  Widget build(BuildContext context) {
    final nickname = comment.userNickname.isEmpty
        ? '匿名用户'
        : comment.userNickname;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.account_circle_outlined, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    nickname,
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                ),
                if (comment.createdAt.isNotEmpty)
                  Text(
                    _formatDateTime(comment.createdAt),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
              ],
            ),
            const SizedBox(height: 10),
            Text(comment.content),
          ],
        ),
      ),
    );
  }
}

String _trimSeconds(String value) {
  if (value.length >= 5) return value.substring(0, 5);
  return value;
}

String _formatDateTime(String value) {
  final normalized = value.replaceFirst('T', ' ');
  if (normalized.length >= 16) return normalized.substring(0, 16);
  return normalized;
}

class _StadiumInfoCard extends StatelessWidget {
  const _StadiumInfoCard({required this.stadium});

  final StadiumDetail stadium;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(stadium.name, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            _IconText(icon: Icons.place_outlined, text: stadium.address),
            _IconText(icon: Icons.phone_outlined, text: stadium.phoneNumber),
            if (stadium.information.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(stadium.information),
            ],
          ],
        ),
      ),
    );
  }
}

class _FieldCard extends StatelessWidget {
  const _FieldCard({
    required this.field,
    required this.submittingSlotId,
    required this.canReserve,
    required this.onReserve,
  });

  final StadiumField field;
  final int submittingSlotId;
  final bool canReserve;
  final ValueChanged<TimeSlot> onReserve;

  @override
  Widget build(BuildContext context) {
    final title = [
      field.fieldType,
      field.number,
    ].where((value) => value.trim().isNotEmpty).join(' ');
    final hasPrice = field.pricePerHour.trim().isNotEmpty;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (title.isNotEmpty || hasPrice) ...[
              Row(
                children: [
                  Expanded(
                    child: Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  if (hasPrice) Text('${field.pricePerHour} 元/小时'),
                ],
              ),
              const SizedBox(height: 12),
            ],
            if (field.timeSlots.isEmpty)
              Text('暂无可约时段。', style: Theme.of(context).textTheme.bodyMedium)
            else
              Column(
                children: [
                  for (final slot in field.timeSlots)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          const Icon(Icons.schedule, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              '${slot.date} ${_trimSeconds(slot.startTime)}-${_trimSeconds(slot.endTime)}',
                            ),
                          ),
                          if (canReserve) ...[
                            const SizedBox(width: 12),
                            FilledButton(
                              onPressed: submittingSlotId == 0
                                  ? () => onReserve(slot)
                                  : null,
                              child: submittingSlotId == slot.id
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Text('预约'),
                            ),
                          ],
                        ],
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

class _MessagePanel extends StatelessWidget {
  const _MessagePanel({required this.icon, required this.message, this.action});

  final IconData icon;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 72),
      child: Center(
        child: Column(
          children: [
            Icon(icon, size: 48, color: Theme.of(context).colorScheme.outline),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            if (action != null) ...[const SizedBox(height: 8), action!],
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

import '../api/comment_api.dart';
import '../api/reservation_api.dart';
import '../api/stadium_api.dart';
import '../models/comment.dart';
import '../models/stadium.dart';
import '../widgets/app_feedback.dart';

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
      // 页面只提交 timeSlotId，预约状态流转和冲突校验都交给后端 API。
      await widget.reservationApi.create(timeSlotId: timeSlotId);
      if (!mounted) return;
      AppFeedback.showMessage(context, '预约已创建，请到我的预约完成支付。');
      await _loadDetail();
    } catch (_) {
      if (!mounted) return;
      AppFeedback.showMessage(context, '预约提交失败，请确认时段仍可预约。', isError: true);
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
      // 详情和评论来自两个接口：场馆详情返回场地/时段，评论接口只返回已审核评论。
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
      AppFeedback.showMessage(context, '请输入评论内容。', isError: true);
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
      AppFeedback.showMessage(context, '评论已提交，等待系统管理员审核。');
      await _loadDetail();
    } catch (_) {
      if (!mounted) return;
      AppFeedback.showMessage(context, '评论提交失败，请稍后重试。', isError: true);
    } finally {
      if (mounted) {
        setState(() {
          isSubmittingComment = false;
        });
      }
    }
  }

  Future<void> _openAllTimeSlots(StadiumField field) async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) => _FieldTimeSlotsScreen(
          field: field,
          submittingSlotId: submittingSlotId,
          canReserve: widget.canReserve,
          onReserve: (slot) => _confirmReservation(field, slot),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        centerTitle: true,
        title: Text(stadium?.name ?? widget.initialName),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadDetail,
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
                    onPressed: _loadDetail,
                    icon: const Icon(Icons.refresh),
                    label: const Text('重试'),
                  ),
                )
              else if (stadium != null) ...[
                if (stadium!.coverImageUrl.trim().isNotEmpty) ...[
                  _StadiumDetailCoverImage(imageUrl: stadium!.coverImageUrl),
                  const SizedBox(height: 16),
                ],
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
                      onViewAll: field.timeSlots.length > 3
                          ? () => _openAllTimeSlots(field)
                          : null,
                    ),
                    const SizedBox(height: 12),
                  ]
                else
                  const AppMessagePanel(
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
                  const AppMessagePanel(
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
                    ? const AppLoadingIcon()
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

class _StadiumDetailCoverImage extends StatelessWidget {
  const _StadiumDetailCoverImage({required this.imageUrl});

  final String imageUrl;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: AspectRatio(
        aspectRatio: 16 / 9,
        child: Image.network(
          imageUrl,
          fit: BoxFit.cover,
          errorBuilder: (context, error, stackTrace) {
            return Container(
              color: const Color(0xFFE5E7EB),
              alignment: Alignment.center,
              child: const Icon(Icons.image_not_supported_outlined, size: 40),
            );
          },
        ),
      ),
    );
  }
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
    required this.onViewAll,
  });

  final StadiumField field;
  final int submittingSlotId;
  final bool canReserve;
  final ValueChanged<TimeSlot> onReserve;
  final VoidCallback? onViewAll;

  @override
  Widget build(BuildContext context) {
    final title = [
      field.fieldType,
      field.number,
    ].where((value) => value.trim().isNotEmpty).join(' ');
    final hasPrice = field.pricePerHour.trim().isNotEmpty;
    final slots = _sortedSlots(field.timeSlots);
    final previewSlots = slots.take(3).toList();

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
            if (slots.isEmpty)
              Text('暂无可约时段。', style: Theme.of(context).textTheme.bodyMedium)
            else
              Column(
                children: [
                  for (final slot in previewSlots)
                    _TimeSlotRow(
                      slot: slot,
                      submittingSlotId: submittingSlotId,
                      canReserve: canReserve,
                      onReserve: onReserve,
                    ),
                  if (onViewAll != null) ...[
                    const SizedBox(height: 4),
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton.icon(
                        onPressed: onViewAll,
                        icon: const Icon(Icons.list_alt_outlined),
                        label: Text('查看全部 ${slots.length} 条'),
                      ),
                    ),
                  ],
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _FieldTimeSlotsScreen extends StatefulWidget {
  const _FieldTimeSlotsScreen({
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
  State<_FieldTimeSlotsScreen> createState() => _FieldTimeSlotsScreenState();
}

class _FieldTimeSlotsScreenState extends State<_FieldTimeSlotsScreen> {
  var selectedDate = '';
  var pendingDate = '';

  @override
  Widget build(BuildContext context) {
    final title = [
      widget.field.fieldType,
      widget.field.number,
    ].where((value) => value.trim().isNotEmpty).join(' ');
    final allSlots = _sortedSlots(widget.field.timeSlots);
    final dateOptions = _slotDates(allSlots);
    final visibleSlots = selectedDate.isEmpty
        ? allSlots
        : allSlots.where((slot) => slot.date == selectedDate).toList();

    return Scaffold(
      appBar: AppBar(
        centerTitle: true,
        title: Text(title.isEmpty ? '可预约时段' : title),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            if (dateOptions.isNotEmpty) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '筛选日期',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 10),
                      InputDecorator(
                        decoration: const InputDecoration(
                          prefixIcon: Icon(Icons.event_outlined),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: pendingDate,
                            isExpanded: true,
                            items: [
                              const DropdownMenuItem(
                                value: '',
                                child: Text('全部日期'),
                              ),
                              for (final date in dateOptions)
                                DropdownMenuItem(
                                  value: date,
                                  child: Text(date),
                                ),
                            ],
                            onChanged: (value) {
                              setState(() {
                                pendingDate = value ?? '';
                              });
                            },
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          FilledButton.icon(
                            onPressed: () {
                              setState(() {
                                selectedDate = pendingDate;
                              });
                            },
                            icon: const Icon(Icons.filter_alt_outlined),
                            label: const Text('筛选'),
                          ),
                          const SizedBox(width: 12),
                          TextButton(
                            onPressed: () {
                              setState(() {
                                pendingDate = '';
                                selectedDate = '';
                              });
                            },
                            child: const Text('重置'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
            ],
            if (visibleSlots.isEmpty)
              const AppMessagePanel(
                icon: Icons.event_busy,
                message: '当前日期暂无可约时段。',
              )
            else
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      for (final slot in visibleSlots)
                        _TimeSlotRow(
                          slot: slot,
                          submittingSlotId: widget.submittingSlotId,
                          canReserve: widget.canReserve,
                          onReserve: widget.onReserve,
                        ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _TimeSlotRow extends StatelessWidget {
  const _TimeSlotRow({
    required this.slot,
    required this.submittingSlotId,
    required this.canReserve,
    required this.onReserve,
  });

  final TimeSlot slot;
  final int submittingSlotId;
  final bool canReserve;
  final ValueChanged<TimeSlot> onReserve;

  @override
  Widget build(BuildContext context) {
    return Padding(
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
              onPressed: submittingSlotId == 0 ? () => onReserve(slot) : null,
              child: submittingSlotId == slot.id
                  ? const AppLoadingIcon()
                  : const Text('预约'),
            ),
          ],
        ],
      ),
    );
  }
}

List<TimeSlot> _sortedSlots(Iterable<TimeSlot> slots) {
  final sorted = slots.toList();
  sorted.sort((a, b) {
    final dateCompare = a.date.compareTo(b.date);
    if (dateCompare != 0) return dateCompare;
    return a.startTime.compareTo(b.startTime);
  });
  return sorted;
}

List<String> _slotDates(Iterable<TimeSlot> slots) {
  final dates = <String>{};
  for (final slot in slots) {
    if (slot.date.isNotEmpty) dates.add(slot.date);
  }
  return dates.toList()..sort();
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

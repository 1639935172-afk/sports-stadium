import 'package:flutter/material.dart';

class AppFeedback {
  static void showMessage(
    BuildContext context,
    String message, {
    bool isError = false,
  }) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError
            ? Theme.of(context).colorScheme.error
            : null,
      ),
    );
  }
}

class AppPageLoading extends StatelessWidget {
  const AppPageLoading({super.key, this.topPadding = 120});

  final double topPadding;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(top: topPadding),
      child: const Center(child: CircularProgressIndicator()),
    );
  }
}

class AppMessagePanel extends StatelessWidget {
  const AppMessagePanel({
    super.key,
    required this.icon,
    required this.message,
    this.action,
    this.topPadding = 72,
  });

  final IconData icon;
  final String message;
  final Widget? action;
  final double topPadding;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(top: topPadding),
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

class AppLoadingIcon extends StatelessWidget {
  const AppLoadingIcon({super.key, this.size = 18});

  final double size;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: const CircularProgressIndicator(strokeWidth: 2),
    );
  }
}

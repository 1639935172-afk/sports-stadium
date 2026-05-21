import 'package:flutter/material.dart';

class AuthBackButton extends StatelessWidget {
  const AuthBackButton({super.key, required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      visualDensity: VisualDensity.compact,
      padding: EdgeInsets.zero,
      constraints: const BoxConstraints.tightFor(width: 36, height: 36),
      onPressed: onPressed,
      icon: const Icon(
        Icons.arrow_back_ios_new,
        color: Color(0xFFC8CDD3),
        size: 24,
      ),
    );
  }
}

class SportLogo extends StatelessWidget {
  const SportLogo({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 56,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          const Positioned.fill(
            left: 4,
            top: 5,
            child: FittedBox(
              alignment: Alignment.centerLeft,
              fit: BoxFit.scaleDown,
              child: Text(
                'SPORT',
                style: TextStyle(
                  color: Color(0xFFF5A8C8),
                  fontSize: 42,
                  fontWeight: FontWeight.w900,
                  fontStyle: FontStyle.italic,
                  letterSpacing: 4,
                ),
              ),
            ),
          ),
          const Positioned(right: -2, top: 0, child: BallIcon()),
        ],
      ),
    );
  }
}

class AuthTitle extends StatelessWidget {
  const AuthTitle({super.key});

  @override
  Widget build(BuildContext context) {
    return const Text(
      '体育场馆预约系统',
      textAlign: TextAlign.center,
      style: TextStyle(
        fontSize: 24,
        fontWeight: FontWeight.w900,
        color: Color(0xFF111827),
      ),
    );
  }
}

class AuthTextField extends StatelessWidget {
  const AuthTextField({
    super.key,
    required this.controller,
    required this.hintText,
    this.keyboardType,
    this.obscureText = false,
    this.textInputAction,
    this.onFieldSubmitted,
    this.validator,
  });

  final TextEditingController controller;
  final String hintText;
  final TextInputType? keyboardType;
  final bool obscureText;
  final TextInputAction? textInputAction;
  final ValueChanged<String>? onFieldSubmitted;
  final String? Function(String?)? validator;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      obscureText: obscureText,
      textInputAction: textInputAction,
      onFieldSubmitted: onFieldSubmitted,
      validator: validator,
      style: const TextStyle(fontSize: 18, color: Color(0xFF111827)),
      decoration: InputDecoration(
        hintText: hintText,
        hintStyle: const TextStyle(
          color: Color(0xFFCFCFCF),
          fontSize: 18,
          fontWeight: FontWeight.w700,
        ),
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 4, vertical: 13),
        border: const OutlineInputBorder(
          borderRadius: BorderRadius.zero,
          borderSide: BorderSide(color: Color(0xFF2B2B2B), width: 1.2),
        ),
        enabledBorder: const OutlineInputBorder(
          borderRadius: BorderRadius.zero,
          borderSide: BorderSide(color: Color(0xFF2B2B2B), width: 1.2),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.zero,
          borderSide: BorderSide(
            color: Theme.of(context).colorScheme.primary,
            width: 1.8,
          ),
        ),
      ),
    );
  }
}

class BallIcon extends StatelessWidget {
  const BallIcon({super.key});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(size: const Size(54, 54), painter: _BallPainter());
  }
}

class _BallPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final border = Paint()
      ..color = const Color(0xFF111827)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.2;
    final blue = Paint()..color = const Color(0xFF2563EB);
    final yellow = Paint()..color = const Color(0xFFF5C84B);
    final line = Paint()
      ..color = const Color(0xFF111827)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    canvas.drawOval(rect.deflate(3), blue);
    final path = Path()
      ..moveTo(size.width * 0.1, size.height * 0.42)
      ..quadraticBezierTo(
        size.width * 0.48,
        size.height * 0.3,
        size.width * 0.92,
        size.height * 0.48,
      )
      ..lineTo(size.width * 0.86, size.height * 0.72)
      ..quadraticBezierTo(
        size.width * 0.46,
        size.height * 0.55,
        size.width * 0.08,
        size.height * 0.66,
      )
      ..close();
    canvas.drawPath(path, yellow);
    canvas.drawOval(rect.deflate(3), border);
    canvas.drawArc(rect.deflate(7), -1.25, 2.4, false, line);
    canvas.drawArc(rect.deflate(8), 1.2, 2.25, false, line);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

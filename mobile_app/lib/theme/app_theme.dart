import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Premium dark theme colors
  static const Color primary = Color(0xFF6C63FF);
  static const Color primaryLight = Color(0xFF8B85FF);
  static const Color secondary = Color(0xFF00D9FF);
  static const Color accent = Color(0xFFFF6584);
  static const Color success = Color(0xFF00E676);
  static const Color warning = Color(0xFFFFAB40);
  static const Color error = Color(0xFFFF5252);
  static const Color surface = Color(0xFF1E1E2E);
  static const Color surfaceLight = Color(0xFF2A2A3E);
  static const Color surfaceLighter = Color(0xFF353550);
  static const Color background = Color(0xFF13131F);
  static const Color textPrimary = Color(0xFFF5F5F5);
  static const Color textSecondary = Color(0xFFA0A0B8);

  // Platform-specific colors
  static Color platformColor(String platform) {
    switch (platform.toLowerCase()) {
      case 'linkedin':
        return const Color(0xFF0A66C2);
      case 'indeed':
        return const Color(0xFF2164F3);
      case 'naukri':
        return const Color(0xFF4A90D9);
      case 'hirist':
        return const Color(0xFFE74C3C);
      case 'glassdoor':
        return const Color(0xFF0CAA41);
      case 'wellfound':
        return const Color(0xFFCC0066);
      default:
        return primary;
    }
  }

  static String platformIcon(String platform) {
    switch (platform.toLowerCase()) {
      case 'linkedin':
        return '💼';
      case 'indeed':
        return '🔍';
      case 'naukri':
        return '🇮🇳';
      case 'hirist':
        return '🎯';
      case 'glassdoor':
        return '🚪';
      case 'wellfound':
        return '🚀';
      default:
        return '📋';
    }
  }

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: secondary,
        surface: surface,
        error: error,
      ),
      textTheme: GoogleFonts.interTextTheme(
        const TextTheme(
          headlineLarge: TextStyle(
            color: textPrimary,
            fontWeight: FontWeight.bold,
            fontSize: 28,
          ),
          headlineMedium: TextStyle(
            color: textPrimary,
            fontWeight: FontWeight.bold,
            fontSize: 22,
          ),
          titleLarge: TextStyle(
            color: textPrimary,
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
          titleMedium: TextStyle(
            color: textPrimary,
            fontWeight: FontWeight.w500,
            fontSize: 16,
          ),
          bodyLarge: TextStyle(color: textPrimary, fontSize: 16),
          bodyMedium: TextStyle(color: textSecondary, fontSize: 14),
          bodySmall: TextStyle(color: textSecondary, fontSize: 12),
        ),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: background,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.inter(
          color: textPrimary,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: surface,
        indicatorColor: primary.withAlpha(50),
        labelTextStyle: WidgetStateProperty.all(
          GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w500),
        ),
      ),
    );
  }
}

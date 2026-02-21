import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Obsidian Tech Theme Colors
  static const Color primary = Color(0xFF00E5FF);    // Electric Cyan
  static const Color secondary = Color(0xFF00FF9C);  // Emerald Tech
  static const Color accent = Color(0xFF7000FF);     // Deep Electric Purple
  static const Color success = Color(0xFF00F5A0);    // Neon Mint
  static const Color warning = Color(0xFFFFB300);    // Amber
  static const Color error = Color(0xFFFF3D00);      // Pure Red
  
  static const Color background = Color(0xFF0B0D15); // Deep Obsidian
  static const Color surface = Color(0xFF161925);    // Dark Surface
  static const Color surfaceLight = Color(0xFF212638);
  static const Color surfaceLighter = Color(0xFF2D334D);
  
  static const Color textPrimary = Color(0xFFE0E6ED);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color textMuted = Color(0xFF64748B);

  // Platform-specific tech colors
  static Color platformColor(String platform) {
    switch (platform.toLowerCase()) {
      case 'linkedin':
        return const Color(0xFF0077B5);
      case 'indeed':
        return const Color(0xFF2164F3);
      case 'naukri':
        return const Color(0xFF4A90D9);
      case 'hirist':
        return const Color(0xFFFF4B2B);
      case 'glassdoor':
        return const Color(0xFF0CAA41);
      case 'wellfound':
        return const Color(0xFFFAFF00);
      default:
        return primary;
    }
  }

  static String platformIcon(String platform) {
    switch (platform.toLowerCase()) {
      case 'linkedin': return '💼';
      case 'indeed': return '🔍';
      case 'naukri': return '🇮🇳';
      case 'hirist': return '🎯';
      case 'glassdoor': return '🚪';
      case 'wellfound': return '🚀';
      default: return '📋';
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
        onSurface: textPrimary,
        error: error,
      ),
      textTheme: GoogleFonts.plusJakartaSansTextTheme(
        const TextTheme(
          headlineLarge: TextStyle(
            color: textPrimary,
            fontWeight: FontWeight.w800,
            fontSize: 30,
            letterSpacing: -0.5,
          ),
          headlineMedium: TextStyle(
            color: textPrimary,
            fontWeight: FontWeight.w700,
            fontSize: 24,
            letterSpacing: -0.5,
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
          bodyLarge: TextStyle(color: textPrimary, fontSize: 16, height: 1.5),
          bodyMedium: TextStyle(color: textSecondary, fontSize: 14, height: 1.5),
          bodySmall: TextStyle(color: textMuted, fontSize: 12),
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        iconTheme: IconThemeData(color: textPrimary),
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xFF262C40), width: 1),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: background,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}

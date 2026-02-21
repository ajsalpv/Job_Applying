import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'theme/app_theme.dart';
import 'screens/dashboard_screen.dart';
import 'screens/platform_screen.dart';
import 'screens/supervisor_screen.dart';
import 'screens/settings_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: AppTheme.surface,
    ),
  );
  runApp(const JobAgentApp());
}

class JobAgentApp extends StatelessWidget {
  const JobAgentApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Job Agent',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const MainNavigation(),
    );
  }
}

class MainNavigation extends StatefulWidget {
  const MainNavigation({super.key});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _currentIndex = 0;

  final List<String> _platforms = [
    'linkedin', 'indeed', 'naukri', 'hirist', 'glassdoor', 'wellfound'
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: [
          const DashboardScreen(),
          // Platform pages
          ...(_platforms.map((p) => PlatformScreen(platform: p))),
          const SupervisorScreen(),
          const SettingsScreen(),
        ],
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(80),
            blurRadius: 20,
            offset: const Offset(0, -5),
          ),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _navItem(0, Icons.dashboard_rounded, 'Home'),
              _navItem(1, Icons.work_rounded, 'Jobs'),
              _navItem(7, Icons.monitor_heart_rounded, 'Agent'),
              _navItem(8, Icons.settings_rounded, 'Settings'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _navItem(int index, IconData icon, String label) {
    final isSelected = _currentIndex == index ||
        (index == 1 && _currentIndex >= 1 && _currentIndex <= 6);
    
    if (index == 1) {
      // Jobs dropdown
      return PopupMenuButton<int>(
        offset: const Offset(0, -280),
        color: AppTheme.surfaceLight,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        onSelected: (val) => setState(() => _currentIndex = val),
        itemBuilder: (context) => _platforms.asMap().entries.map((entry) {
          return PopupMenuItem<int>(
            value: entry.key + 1,
            child: Row(
              children: [
                Text(
                  AppTheme.platformIcon(entry.value),
                  style: const TextStyle(fontSize: 20),
                ),
                const SizedBox(width: 12),
                Text(
                  entry.value[0].toUpperCase() + entry.value.substring(1),
                  style: TextStyle(
                    color: _currentIndex == entry.key + 1
                        ? AppTheme.primary
                        : AppTheme.textPrimary,
                    fontWeight: _currentIndex == entry.key + 1
                        ? FontWeight.bold
                        : FontWeight.normal,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
        child: _buildNavIcon(icon, label, isSelected),
      );
    }

    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      child: _buildNavIcon(icon, label, isSelected),
    );
  }

  Widget _buildNavIcon(IconData icon, String label, bool isSelected) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: isSelected
            ? AppTheme.primary.withAlpha(30)
            : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: isSelected ? AppTheme.primary : AppTheme.textSecondary,
            size: 24,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: isSelected ? AppTheme.primary : AppTheme.textSecondary,
              fontSize: 11,
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }
}

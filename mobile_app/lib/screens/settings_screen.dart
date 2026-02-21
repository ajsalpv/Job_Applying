import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _locationController = TextEditingController();
  final _rolesController = TextEditingController();
  
  int _experienceYears = 1;
  bool _loading = false;
  bool _saving = false;
  bool _connected = false;
  String _serverStatus = 'Checking connection...';

  @override
  void initState() {
    super.initState();
    _loadSettings();
    _checkHealth();
  }

  Future<void> _checkHealth() async {
    try {
      final health = await ApiService.getHealth();
      if (mounted) {
        setState(() {
          _connected = true;
          _serverStatus = 'Connected to ${health['service'] ?? 'Backend'}';
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _connected = false;
          _serverStatus = 'Cannot connect to backend';
        });
      }
    }
  }

  Future<void> _loadSettings() async {
    setState(() => _loading = true);
    try {
      final settings = await ApiService.getAppSettings();
      if (mounted) {
        setState(() {
          _locationController.text = settings['user_location'] ?? '';
          _rolesController.text = settings['target_roles'] ?? '';
          _experienceYears = settings['experience_years'] ?? 1;
        });
      }
    } catch (e) {
      debugPrint('Settings load error: $e');
      // Fallback to defaults shown in app if backend is down
      if (mounted) {
        _locationController.text = "Bangalore, Remote, Hyderabad"; // Minimal default
        _rolesController.text = "AI Engineer, ML Engineer";
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _saveSettings() async {
    setState(() => _saving = true);
    try {
      await ApiService.updateAppSettings({
        'user_location': _locationController.text.trim(),
        'target_roles': _rolesController.text.trim(),
        'experience_years': _experienceYears,
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('✅ Preferences saved successfully!'), backgroundColor: AppTheme.success),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('❌ Save failed: $e'), backgroundColor: AppTheme.error),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () { _loadSettings(); _checkHealth(); },
          ),
        ],
      ),
      body: _loading 
        ? const Center(child: CircularProgressIndicator())
        : ListView(
            padding: const EdgeInsets.all(20),
            children: [
              // Server Status Indicator
              _buildCard(
                child: Row(
                  children: [
                    Container(
                      width: 12, height: 12,
                      decoration: BoxDecoration(
                        color: _connected ? AppTheme.success : AppTheme.error,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Backend Status', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                          Text(_serverStatus, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                        ],
                      ),
                    ),
                    Text(
                      'v1.0.0',
                      style: TextStyle(fontSize: 10, color: AppTheme.textSecondary.withAlpha(100)),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),
              _buildSectionHeader('JOB SEARCH PREFERENCES'),
              _buildCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildTextField(
                      controller: _locationController,
                      label: 'Target Locations',
                      icon: Icons.location_on_rounded,
                      hint: 'Bangalore, Remote, etc.',
                    ),
                    const SizedBox(height: 24),
                    _buildTextField(
                      controller: _rolesController,
                      label: 'Target Roles',
                      icon: Icons.work_rounded,
                      hint: 'AI Engineer, ML Engineer',
                    ),
                    const SizedBox(height: 32),
                    const Text(
                      'Experience required (Years)',
                      style: TextStyle(color: AppTheme.textSecondary, fontSize: 13, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.trending_up_rounded, size: 20, color: AppTheme.primary),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Slider(
                            value: _experienceYears.toDouble(),
                            min: 0,
                            max: 10,
                            divisions: 10,
                            label: '$_experienceYears years',
                            activeColor: AppTheme.primary,
                            onChanged: (val) => setState(() => _experienceYears = val.toInt()),
                          ),
                        ),
                        Text(
                          '$_experienceYears yrs',
                          style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 40),
              SizedBox(
                height: 54,
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: _saving ? null : _saveSettings,
                  icon: _saving 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.check_circle_rounded),
                  label: const Text('Save Preferences', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppTheme.primary,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const Center(
                child: Text(
                  'Connected to: job-applying-agent.onrender.com',
                  style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                ),
              ),
              const SizedBox(height: 60),
            ],
          ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 12),
      child: Text(
        title,
        style: const TextStyle(
          color: AppTheme.primary,
          fontSize: 12,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  Widget _buildCard({required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.surfaceLighter),
      ),
      child: child,
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    required String hint,
  }) {
    return TextField(
      controller: controller,
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: AppTheme.textSecondary, fontSize: 13, fontWeight: FontWeight.bold),
        hintText: hint,
        hintStyle: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
        prefixIcon: Icon(icon, color: AppTheme.primary, size: 20),
        enabledBorder: const UnderlineInputBorder(borderSide: BorderSide(color: AppTheme.surfaceLighter)),
        focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: AppTheme.primary)),
      ),
    );
  }

  @override
  void dispose() {
    _locationController.dispose();
    _rolesController.dispose();
    super.dispose();
  }
}

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

class JobDetailScreen extends StatefulWidget {
  final dynamic job;
  const JobDetailScreen({super.key, required this.job});

  @override
  State<JobDetailScreen> createState() => _JobDetailScreenState();
}

class _JobDetailScreenState extends State<JobDetailScreen> {
  bool _updating = false;

  Future<void> _markAsApplied() async {
    setState(() => _updating = true);
    try {
      await ApiService.updateStatus(
        widget.job['company'],
        widget.job['role'],
        'applied',
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('🎉 Job marked as Applied!'), backgroundColor: AppTheme.success),
        );
        Navigator.pop(context, true); // Return true to refresh list
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: $e'), backgroundColor: AppTheme.error),
        );
      }
    } finally {
      if (mounted) setState(() => _updating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final job = widget.job;
    final platform = job['platform'] ?? 'linkedin';
    final platformColor = AppTheme.platformColor(platform);
    final score = job['fit_score'] ?? 0;
    final isApplied = job['status']?.toString().toLowerCase() == 'applied';

    return Scaffold(
      backgroundColor: AppTheme.background,
      body: CustomScrollView(
        slivers: [
          // Elegant Header
          SliverAppBar(
            expandedHeight: 180,
            pinned: true,
            backgroundColor: AppTheme.surface,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.bottomCenter,
                    end: Alignment.topCenter,
                    colors: [
                      AppTheme.background,
                      platformColor.withAlpha(40),
                    ],
                  ),
                ),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(height: 40),
                      Text(AppTheme.platformIcon(platform), style: const TextStyle(fontSize: 48)),
                      const SizedBox(height: 8),
                      Text(
                        platform[0].toUpperCase() + platform.substring(1),
                        style: TextStyle(color: platformColor, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title & Company
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              job['role'] ?? 'Unknown Role',
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              job['company'] ?? 'Unknown Company',
                              style: TextStyle(color: platformColor, fontSize: 18, fontWeight: FontWeight.w500),
                            ),
                          ],
                        ),
                      ),
                      _scoreBadge(score),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Info Row
                  Row(
                    children: [
                      _infoChip(Icons.location_on_rounded, job['location'] ?? 'Remote'),
                      const SizedBox(width: 12),
                      _infoChip(Icons.calendar_today_rounded, job['date'] ?? 'Jan 1'),
                    ],
                  ),
                  const SizedBox(height: 30),

                  // Tabs-like sections
                  _sectionHeader(Icons.description_rounded, 'Job Description'),
                  _contentBox(job['job_description'] ?? 'No description available.'),
                  
                  const SizedBox(height: 24),
                  _sectionHeader(Icons.psychology_rounded, 'Interview Preparation'),
                  _contentBox(job['interview_prep'] ?? 'Wait for discovery to complete...'),

                  const SizedBox(height: 24),
                  _sectionHeader(Icons.auto_awesome_rounded, 'Skills to Learn'),
                  _contentBox(job['skills_to_learn'] ?? 'Enhancement in progress...'),

                  const SizedBox(height: 24),
                  _sectionHeader(Icons.notes_rounded, 'Notes'),
                  _contentBox(job['notes'] ?? 'No additional notes.'),

                  const SizedBox(height: 40),
                  
                  // Action Buttons
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () async {
                            final url = job['job_url'] ?? '';
                            if (url.isNotEmpty) {
                              await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
                            }
                          },
                          icon: const Icon(Icons.open_in_new_rounded),
                          label: const Text('Open Original'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            side: BorderSide(color: platformColor),
                            foregroundColor: platformColor,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      if (!isApplied)
                        Expanded(
                          child: FilledButton.icon(
                            onPressed: _updating ? null : _markAsApplied,
                            icon: _updating 
                              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                              : const Icon(Icons.check_circle_rounded),
                            label: const Text('Mark Applied'),
                            style: FilledButton.styleFrom(
                              backgroundColor: AppTheme.primary,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _scoreBadge(int score) {
    final color = score >= 80 ? AppTheme.success : score >= 60 ? AppTheme.warning : AppTheme.error;
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: color.withAlpha(20),
            shape: BoxShape.circle,
            border: Border.all(color: color.withAlpha(100)),
          ),
          child: Text(
            '$score',
            style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 20),
          ),
        ),
        const SizedBox(height: 4),
        Text('FIT SCORE', style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _infoChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.surfaceLighter),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: AppTheme.textSecondary),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _sectionHeader(IconData icon, String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppTheme.primary),
          const SizedBox(width: 10),
          Text(
            title.toUpperCase(),
            style: const TextStyle(
              color: AppTheme.primary,
              fontWeight: FontWeight.bold,
              fontSize: 13,
              letterSpacing: 1.2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _contentBox(String content) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.surfaceLighter),
      ),
      child: Text(
        content,
        style: const TextStyle(
          color: AppTheme.textPrimary,
          fontSize: 15,
          height: 1.5,
        ),
      ),
    );
  }
}

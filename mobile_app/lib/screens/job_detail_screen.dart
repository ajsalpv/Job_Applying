import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';

class JobDetailScreen extends StatelessWidget {
  final dynamic job;
  const JobDetailScreen({super.key, required this.job});

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.platformColor(job['platform'] ?? '');
    final score = job['fit_score'] ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: Text(job['company'] ?? 'Job Details'),
        actions: [
          IconButton(
            icon: Icon(Icons.open_in_new_rounded, color: color),
            onPressed: () async {
              final url = job['job_url'] ?? '';
              if (url.isNotEmpty) {
                await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
              }
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Header Card
          _buildHeaderCard(context, color, score),
          const SizedBox(height: 20),

          // Job Description
          _buildSection(
            context,
            title: '📋 Job Description',
            content: job['job_description'] ?? 'No description available.',
            color: AppTheme.primary,
          ),
          const SizedBox(height: 16),

          // Interview Preparation
          _buildSection(
            context,
            title: '🎯 Interview Preparation',
            content: job['interview_prep'] ?? 'No interview prep data yet.\n\nTrigger a scan to generate insights!',
            color: AppTheme.success,
          ),
          const SizedBox(height: 16),

          // Skills to Learn
          _buildSection(
            context,
            title: '📚 Skills to Learn',
            content: job['skills_to_learn'] ?? 'No skill analysis available yet.',
            color: AppTheme.secondary,
          ),
          const SizedBox(height: 16),

          // Notes
          if ((job['notes'] ?? '').toString().isNotEmpty)
            _buildSection(
              context,
              title: '📝 Notes',
              content: job['notes'] ?? '',
              color: AppTheme.warning,
            ),
          const SizedBox(height: 24),

          // Open Job Link Button
          _buildOpenButton(color),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildHeaderCard(BuildContext context, Color color, int score) {
    final scoreColor = score >= 80 ? AppTheme.success
        : score >= 60 ? AppTheme.warning
        : AppTheme.error;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            color.withAlpha(40),
            color.withAlpha(15),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withAlpha(60)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                AppTheme.platformIcon(job['platform'] ?? ''),
                style: const TextStyle(fontSize: 32),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      job['role'] ?? 'Unknown Role',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      job['company'] ?? '',
                      style: TextStyle(
                        fontSize: 15,
                        color: color,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          // Info chips
          Wrap(
            spacing: 10,
            runSpacing: 8,
            children: [
              _infoChip(Icons.location_on_rounded, job['location'] ?? 'Unknown', color),
              _infoChip(Icons.calendar_today_rounded, job['date'] ?? 'Today', color),
              _infoChip(Icons.star_rounded, 'Score: $score%', scoreColor),
              _statusChip(job['status'] ?? 'unknown'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _infoChip(IconData icon, String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLight,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 5),
          Text(text, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }

  Widget _statusChip(String status) {
    final color = _statusColor(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withAlpha(60)),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildSection(BuildContext context, {
    required String title,
    required String content,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.surfaceLighter),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 4, height: 24,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 10),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          // Parse and render content with sections
          ..._parseContent(content),
        ],
      ),
    );
  }

  List<Widget> _parseContent(String content) {
    final lines = content.split('\n');
    List<Widget> widgets = [];

    for (var line in lines) {
      line = line.trim();
      if (line.isEmpty) {
        widgets.add(const SizedBox(height: 8));
      } else if (line.startsWith('•') || line.startsWith('-') || line.startsWith('*')) {
        widgets.add(
          Padding(
            padding: const EdgeInsets.only(left: 8, bottom: 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('• ', style: TextStyle(color: AppTheme.primary, fontSize: 14, fontWeight: FontWeight.bold)),
                Expanded(
                  child: Text(
                    line.substring(1).trim(),
                    style: const TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 14,
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      } else if (line.contains(':') && line.length < 60 && !line.contains('http')) {
        // Looks like a heading/label
        widgets.add(
          Padding(
            padding: const EdgeInsets.only(top: 8, bottom: 4),
            child: Text(
              line,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        );
      } else {
        widgets.add(
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Text(
              line,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 14,
                height: 1.6,
              ),
            ),
          ),
        );
      }
    }

    return widgets;
  }

  Widget _buildOpenButton(Color color) {
    return SizedBox(
      width: double.infinity,
      height: 54,
      child: FilledButton.icon(
        onPressed: () async {
          final url = job['job_url'] ?? '';
          if (url.isNotEmpty) {
            await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
          }
        },
        icon: const Icon(Icons.open_in_new_rounded),
        label: const Text('Open Job Listing', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        style: FilledButton.styleFrom(
          backgroundColor: color,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
    );
  }

  Color _statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'applied': return AppTheme.primary;
      case 'interview': return AppTheme.success;
      case 'offer': return AppTheme.warning;
      case 'rejected': return AppTheme.error;
      default: return AppTheme.textSecondary;
    }
  }
}

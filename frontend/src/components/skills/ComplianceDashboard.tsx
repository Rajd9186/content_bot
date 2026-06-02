'use client';

import { useState, useEffect } from 'react';
import type { SkillAnalytics } from '@/types/skills';
import { skillsApi } from '@/lib/skills-api';
import { BarChart3, TrendingUp, Award, Clock } from 'lucide-react';

export function ComplianceDashboard() {
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<SkillAnalytics | null>(null);
  const [topSkills, setTopSkills] = useState<SkillAnalytics[]>([]);
  const [working, setWorking] = useState(false);

  useEffect(() => {
    loadTopSkills();
  }, []);

  useEffect(() => {
    if (selectedSkillId) {
      loadAnalytics(selectedSkillId);
    } else {
      setAnalytics(null);
    }
  }, [selectedSkillId]);

  const loadTopSkills = async () => {
    setWorking(true);
    try {
      const data = await skillsApi.getTopSkills();
      setTopSkills(data);
    } catch (err) {
      console.error('Failed to load top skills:', err);
    } finally {
      setWorking(false);
    }
  };

  const loadAnalytics = async (id: string) => {
    setWorking(true);
    try {
      const data = await skillsApi.getAnalytics(id);
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setWorking(false);
    }
  };

  const getComplianceColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getRatingColor = (score: number) => {
    if (score >= 4) return 'bg-emerald-500';
    if (score >= 2.5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="p-6 space-y-4 h-full overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-emerald-400" />
          Compliance Dashboard
        </h2>
      </div>

      {working && topSkills.length === 0 ? (
        <div className="text-center text-gray-500 py-12">
          <p>Loading compliance data...</p>
        </div>
      ) : topSkills.length === 0 ? (
        <div className="text-center text-gray-500 py-12 border border-dashed border-gray-700 rounded-lg">
          <BarChart3 className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <p>No compliance data available yet. Run a pipeline with skills to see results.</p>
        </div>
      ) : (
        <div className="flex gap-6">
          <div className="w-[40%] shrink-0">
            <div className="bg-gray-900 rounded-lg border border-gray-700">
              <div className="px-4 py-3 border-b border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  Top Skills by Usage
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700 text-xs text-gray-500 uppercase">
                      <th className="text-left px-4 py-2 font-medium">Rank</th>
                      <th className="text-left px-4 py-2 font-medium">Skill Name</th>
                      <th className="text-right px-4 py-2 font-medium">Usage</th>
                      <th className="text-right px-4 py-2 font-medium">Avg Compliance</th>
                      <th className="text-right px-4 py-2 font-medium">Avg Rating</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topSkills.map((skill, index) => (
                      <tr
                        key={skill.skill_id}
                        onClick={() => setSelectedSkillId(skill.skill_id)}
                        className={`border-b border-gray-800 cursor-pointer transition-colors hover:bg-gray-800 ${
                          selectedSkillId === skill.skill_id ? 'bg-gray-800' : ''
                        }`}
                      >
                        <td className="px-4 py-3 text-gray-400">{index + 1}</td>
                        <td className="px-4 py-3 text-white font-medium">{skill.skill_id}</td>
                        <td className="px-4 py-3 text-gray-300 text-right">{skill.usage_count}</td>
                        <td className="px-4 py-3 text-right">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            skill.average_compliance >= 80
                              ? 'text-emerald-400 bg-emerald-900/30'
                              : skill.average_compliance >= 50
                              ? 'text-yellow-400 bg-yellow-900/30'
                              : 'text-red-400 bg-red-900/30'
                          }`}>
                            {skill.average_compliance.toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            skill.average_rating >= 4
                              ? 'text-emerald-400 bg-emerald-900/30'
                              : skill.average_rating >= 2.5
                              ? 'text-yellow-400 bg-yellow-900/30'
                              : 'text-red-400 bg-red-900/30'
                          }`}>
                            {skill.average_rating.toFixed(1)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="flex-1">
            {!selectedSkillId ? (
              <div className="bg-gray-900 rounded-lg border border-gray-700 p-8 text-center text-gray-500">
                <BarChart3 className="w-10 h-10 mx-auto mb-2 text-gray-600" />
                <p>Select a skill from the list to view details.</p>
              </div>
            ) : !analytics ? (
              <div className="bg-gray-900 rounded-lg border border-gray-700 p-8 text-center text-gray-500">
                <p>Loading analytics...</p>
              </div>
            ) : (
              <div className="bg-gray-900 rounded-lg border border-gray-700 p-6 space-y-5">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Award className="w-5 h-5 text-emerald-400" />
                    <h3 className="text-lg font-semibold text-white">{analytics.skill_id}</h3>
                  </div>
                  <p className="text-xs text-gray-500">Skill ID: {analytics.skill_id}</p>
                </div>

                <div className="flex items-center gap-3 bg-gray-800 rounded-lg px-4 py-3 border border-gray-700">
                  <BarChart3 className="w-6 h-6 text-emerald-400 shrink-0" />
                  <div>
                    <p className="text-xs text-gray-500">Usage Count</p>
                    <p className="text-2xl font-bold text-white">{analytics.usage_count.toLocaleString()}</p>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Compliance Score</span>
                    <span className={`text-sm font-semibold ${
                      analytics.average_compliance >= 80 ? 'text-emerald-400' : analytics.average_compliance >= 50 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {analytics.average_compliance.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all ${getComplianceColor(analytics.average_compliance)}`}
                      style={{ width: `${Math.min(analytics.average_compliance, 100)}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Rating</span>
                    <span className={`text-sm font-semibold ${
                      analytics.average_rating >= 4 ? 'text-emerald-400' : analytics.average_rating >= 2.5 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {analytics.average_rating.toFixed(1)} / 5
                    </span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all ${getRatingColor(analytics.average_rating)}`}
                      style={{ width: `${(analytics.average_rating / 5) * 100}%` }}
                    />
                  </div>
                </div>

                {analytics.last_used && (
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Clock className="w-4 h-4" />
                    <span>Last used: {new Date(analytics.last_used).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

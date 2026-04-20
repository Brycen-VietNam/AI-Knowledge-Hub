// Spec: docs/admin-spa/spec/admin-spa.spec.md#S003
// Task: T006 — UsersGroupsPage — tabbed container: Groups + Users
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAdminGuard } from '../hooks/useAdminGuard'
import { GroupsTab } from '../components/GroupsTab'
import { UsersTab } from '../components/UsersTab'

export function UsersGroupsPage() {
  const { t } = useTranslation()
  useAdminGuard()

  const [activeTab, setActiveTab] = useState<'groups' | 'users'>('groups')

  return (
    <div className="users-groups-page">
      <h1>{t('users_groups_page_title')}</h1>
      <div className="tab-bar">
        <button
          onClick={() => setActiveTab('groups')}
          className={activeTab === 'groups' ? 'active' : ''}
        >
          {t('tab_groups')}
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={activeTab === 'users' ? 'active' : ''}
        >
          {t('tab_users')}
        </button>
      </div>
      {activeTab === 'groups' ? <GroupsTab /> : <UsersTab />}
    </div>
  )
}

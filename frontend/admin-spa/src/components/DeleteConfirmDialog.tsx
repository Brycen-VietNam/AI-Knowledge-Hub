// Spec: docs/admin-spa/spec/admin-spa.spec.md#S002
// Task: T002 — DeleteConfirmDialog — generic confirm dialog
interface DeleteConfirmDialogProps {
  open: boolean
  title: string
  message: string
  onConfirm: () => void
  onCancel: () => void
}

export function DeleteConfirmDialog({ open, title, message, onConfirm, onCancel }: DeleteConfirmDialogProps) {
  if (!open) return null

  return (
    <div className="confirm-dialog-overlay" onClick={onCancel}>
      <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        <p>{message}</p>
        <div className="confirm-dialog-actions">
          <button className="btn-secondary" onClick={onCancel}>Cancel</button>
          <button className="btn-danger" onClick={onConfirm}>Delete</button>
        </div>
      </div>
    </div>
  )
}

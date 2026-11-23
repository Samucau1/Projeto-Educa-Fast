import React, { createContext, useContext, useRef, useState } from 'react';
import { ActionDialog, DialogContext } from './ActionDialog';
import { api } from '../api';

export const PageDataContext = createContext({ refresh: async () => {} });

export function MutationForm({ modalTitle, modalLabel, ...props }) {
    return modalTitle ? <ActionDialog title={modalTitle} label={modalLabel || modalTitle}><MutationBody {...props} /></ActionDialog> : <MutationBody {...props} />;
}

function MutationBody({ action, resetOnSuccess = false, children, ...props }) {
    const modal = useContext(DialogContext);
    const { refresh } = useContext(PageDataContext);
    const [pending, setPending] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const submitting = useRef(false);

    async function submit(event) {
        event.preventDefault();
        if (submitting.current) return;
        submitting.current = true;
        const form = event.currentTarget;
        const payload = new FormData(form);
        setPending(true);
        modal?.setBusy(true);
        setFeedback(null);
        try {
            const result = await api(action, { method: 'POST', body: payload });
            if (resetOnSuccess) form.reset();
            setFeedback({ success: true, message: result.mensagem || 'Operação realizada com sucesso.' });
            await refresh();
        } catch (error) {
            setFeedback({ success: false, message: error.message });
        } finally {
            submitting.current = false;
            setPending(false);
            modal?.setBusy(false);
        }
    }

    return <form {...props} action={action} method="post" onSubmit={submit} aria-busy={pending}>
        {children}
        {pending && <p role="status" className="text-sm text-cyan-200">Salvando…</p>}
        {feedback && <p role={feedback.success ? 'status' : 'alert'} className={`form-feedback ${feedback.success ? 'text-green-200' : 'text-red-200'}`}>{feedback.message}</p>}
    </form>;
}

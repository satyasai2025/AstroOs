import { redirect } from 'next/navigation';

export default function KPPage() {
  redirect('/charts?view=kp');
}

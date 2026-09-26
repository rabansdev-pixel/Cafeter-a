import React, { useEffect, useState } from 'react';
import { Home, Package, Tags, Boxes, Users, Activity, PanelLeftClose, PanelLeftOpen, ExternalLink, User, LogOut, ArrowUpRight, Plus, Clock3, CircleAlert } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export type DashboardData = {
  section: string; name: string; role: string;
  navigation: {key: string; label: string; href: string}[];
  stats: {label: string; value: number; note: string; icon: string; section: string}[];
  activity: {id: number; title: string; description: string; time: string}[];
  canViewActivity: boolean;
  stock: {out: number; unknown: number};
  products: {id: number; name: string; image: string; price: string; href: string}[];
  urls: {site: string; account: string; logout: string; create: string; inventory: string; activity: string};
};
const icons: Record<string, LucideIcon> = {dashboard: Home, products: Package, categories: Tags, inventory: Boxes, users: Users, activity: Activity};

export function Sidebar({data}: {data: DashboardData}) {
  const [open, setOpen] = useState(() => {
    if (window.matchMedia('(max-width: 767px)').matches) return false;
    try { return localStorage.getItem('zd-admin-sidebar') !== 'collapsed'; } catch { return true; }
  });
  useEffect(() => {
    const shell = document.querySelector<HTMLElement>('.admin-shell');
    if (shell) shell.dataset.collapsed = String(!open);
    try { localStorage.setItem('zd-admin-sidebar', open ? 'expanded' : 'collapsed'); } catch { /* Storage is optional. */ }
  }, [open]);
  const csrf = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content || '';
  return <div className={`zd-sidebar ${open ? '' : 'is-collapsed'}`}>
    <a className="zd-workspace" href={data.navigation[0].href} title="ZERO DAY · Administración">
      <span className="zd-mark">ZD<span>·</span></span>
      <span className="zd-nav-label"><strong>ZERO DAY</strong><small>Administración</small></span>
    </a>
    <nav id="admin-navigation" aria-label="Administración">
      {data.navigation.map(item => {
        const Icon = icons[item.key] || Package;
        return <a key={item.key} href={item.href} aria-label={item.label} title={item.label} aria-current={data.section === item.key ? 'page' : undefined}>
          <Icon size={18} aria-hidden="true"/><span className="zd-nav-label">{item.label}</span>
        </a>;
      })}
    </nav>
    <div className="zd-nav-secondary">
      <a href={data.urls.site} title="Ver sitio" aria-label="Ver sitio"><ExternalLink size={18} aria-hidden="true"/><span className="zd-nav-label">Ver sitio</span></a>
      <a href={data.urls.account} title="Mi cuenta" aria-label="Mi cuenta"><User size={18} aria-hidden="true"/><span className="zd-nav-label">Mi cuenta</span></a>
    </div>
    <div className="zd-sidebar-bottom">
      <div className="zd-person zd-nav-label"><strong>{data.name}</strong><small>{data.role}</small></div>
      <form method="post" action={data.urls.logout}><input type="hidden" name="csrf_token" value={csrf}/><button type="submit" title="Cerrar sesión" aria-label="Cerrar sesión"><LogOut size={18} aria-hidden="true"/><span className="zd-nav-label">Cerrar sesión</span></button></form>
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="admin-navigation" aria-label={open ? 'Contraer menú' : 'Expandir menú'} title={open ? 'Contraer menú' : 'Expandir menú'}>
        {open ? <PanelLeftClose size={18} aria-hidden="true"/> : <PanelLeftOpen size={18} aria-hidden="true"/>}<span className="zd-nav-label">Contraer menú</span>
      </button>
    </div>
  </div>;
}

export const Example = ({data}: {data: DashboardData}) => <div className="zd-dashboard">
  <div className="zd-overview-intro"><p>Tu carta, tus existencias y los últimos cambios.</p><a className="zd-primary" href={data.urls.create}><Plus size={17} aria-hidden="true"/> Añadir producto</a></div>
  <div className="zd-stats tw:grid tw:gap-4">
    {data.stats.map(stat => { const Icon = icons[stat.icon] || Package; return <a key={stat.label} className="zd-stat" href={data.navigation.find(n => n.key === stat.section)?.href}>
      <span className="zd-stat-top"><Icon size={19} aria-hidden="true"/><ArrowUpRight size={15} aria-hidden="true"/></span>
      <h2>{stat.label}</h2><strong>{stat.value.toLocaleString('es-EC')}</strong><p>{stat.note}</p>
    </a>; })}
  </div>
  <div className="zd-content-grid">
    <section className="zd-panel">
      <header><div><span className="zd-eyebrow">{data.canViewActivity ? 'REGISTRO DE CAMBIOS' : 'CARTA DE ZERO DAY'}</span><h2>{data.canViewActivity ? 'Actividad reciente' : 'Productos recientes'}</h2></div>{data.canViewActivity && <a href={data.urls.activity}>Ver todo <ArrowUpRight size={14} aria-hidden="true"/></a>}</header>
      {data.canViewActivity ? <div className="zd-activity">
        {data.activity.length ? data.activity.map(item => <article key={item.id}>
          <span className="zd-event-icon"><Activity size={17} aria-hidden="true"/></span>
          <div><h3>{item.title}</h3><p>{item.description}</p><time dateTime={item.time}>{new Date(item.time).toLocaleString('es-EC', {dateStyle:'medium', timeStyle:'short'})}</time></div>
        </article>) : <p className="zd-empty">Aún no hay cambios registrados.</p>}
      </div> : <ProductList products={data.products}/>}
    </section>
    <div className="zd-right-column">
      <section className="zd-panel zd-inventory"><header><div><span className="zd-eyebrow">EXISTENCIAS</span><h2>Antes de abrir</h2></div><CircleAlert size={19} aria-hidden="true"/></header>
        <dl><div><dt>Productos agotados</dt><dd>{data.stock.out}</dd></div><div><dt>Stock sin registrar</dt><dd>{data.stock.unknown}</dd></div></dl>
        <a className="zd-secondary" href={data.urls.inventory}>Revisar inventario <ArrowUpRight size={16} aria-hidden="true"/></a>
      </section>
      {data.canViewActivity && <section className="zd-panel"><header><div><span className="zd-eyebrow">ÚLTIMAS EDICIONES</span><h2>Tu carta</h2></div><Clock3 size={18} aria-hidden="true"/></header><ProductList products={data.products}/></section>}
    </div>
  </div>
</div>;

function ProductList({products}: {products: DashboardData['products']}) {
  return <div className="zd-recent-products">{products.length ? products.map(p => <a href={p.href} key={p.id}><img src={p.image} alt="" width="48" height="48" loading="lazy"/><span>{p.name}<small>{p.price}</small></span><ArrowUpRight size={15} aria-hidden="true"/></a>) : <p className="zd-empty">Todavía no hay productos.</p>}</div>;
}
export default Example;

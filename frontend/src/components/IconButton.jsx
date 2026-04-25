export default function IconButton({ icon: Icon, children, className = "", ...props }) {
  return (
    <button className={`icon-button ${className}`} type="button" {...props}>
      {Icon ? <Icon size={18} strokeWidth={2.2} /> : null}
      <span>{children}</span>
    </button>
  );
}
